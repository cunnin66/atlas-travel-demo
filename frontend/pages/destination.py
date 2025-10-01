import os
import sys

import streamlit as st
from components.menu import menu_with_redirect
from utils import request_with_auth

TAG_OPTIONS = [
    "Beach",
    "Mountain",
    "Cultural",
    "Historical",
    "Food",
    "Shopping",
    "Nightlife",
]


def save_destination(id, name, description, lat, lon, tags=[]):
    response = request_with_auth(
        "PUT",
        f"/destinations/{id}",
        json={
            "name": name,
            "description": description,
            "latitude": lat,
            "longitude": lon,
            "tags": tags,
        },
    )
    if response.status_code == 200:
        st.success(f"Destination '{name}' saved successfully!")
    else:
        st.error(
            f"Error: Unable to save destination (status code {response.status_code})"
        )


def get_destination(destination_id):
    response = request_with_auth("GET", f"/destinations/{destination_id}")
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_knowledge_items(destination_id=None):
    """Get knowledge base items, optionally filtered by destination"""
    url = "/knowledge/"
    if destination_id is not None:
        url += f"?destination_id={destination_id}"

    response = request_with_auth("GET", url)
    if response.status_code == 200:
        return response.json()
    else:
        return []


def upload_knowledge_file(file, title=None, destination_id=None):
    """Upload a file to the knowledge base"""
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {}
    if title:
        data["title"] = title
    if destination_id:
        data["destination_id"] = destination_id

    response = request_with_auth(
        "POST", "/knowledge/upload-file", files=files, data=data
    )
    return response


def search_knowledge_base(query, limit=5, destination_id=None):
    """Search the knowledge base"""
    search_data = {"query": query, "limit": limit}
    if destination_id is not None:
        search_data["destination_id"] = destination_id

    response = request_with_auth("POST", "/knowledge/search", json=search_data)
    if response.status_code == 200:
        return response.json()
    else:
        return None


if "edit_destination" in st.session_state:
    destination = get_destination(st.session_state.edit_destination)
else:
    destination = None

# Get knowledge items for display (filtered by destination)
destination_id = st.session_state.get("edit_destination") if destination else None
knowledge_items = get_knowledge_items(destination_id)
menu_with_redirect()

if destination is None:
    st.subheader("Unknown Destination!")

    st.markdown(
        """
    Oops! There was an error: no destination data found. Please navigate back to the [Home Page](./home) to choose a destination.
    """
    )
    if st.button("< Back", type="secondary"):
        st.switch_page("pages/home.py")

else:
    st.subheader(f"Destination Editor: {destination['name']}")

    cols = st.columns(2, gap="large")
    with cols[0]:
        st.write("EDITOR")
        name = st.text_input("Destination Name", value=destination["name"])
        description = st.text_area("Description", value=destination["description"])
        with st.container(horizontal=True):
            lat = st.number_input("Latitude", value=destination["latitude"])
            lon = st.number_input("Longitude", value=destination["longitude"])
        tags = st.multiselect("Tags", default=destination["tags"], options=TAG_OPTIONS)
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("< Back", type="secondary"):
                st.switch_page("pages/home.py")
            if st.button("Save", type="primary"):
                save_destination(
                    destination["id"],
                    name if name else destination["name"],
                    description if description else destination["description"],
                    lat if lat is not None else destination.get("latitude"),
                    lon if lon is not None else destination.get("longitude"),
                    tags if tags else destination.get("tags", []),
                )

    with cols[1]:
        with st.container(border=True):
            st.write("KNOWLEDGE BASE")

            # Display existing knowledge items
            if len(knowledge_items) > 0:
                st.write("**Uploaded Files:**")
                for item in knowledge_items:
                    with st.expander(f"📄 {item['title']}", expanded=False):
                        st.write(f"**Type:** {item['source_type']}")
                        if item.get("item_metadata", {}).get("file_size"):
                            file_size_kb = item["item_metadata"]["file_size"] / 1024
                            st.write(f"**Size:** {file_size_kb:.1f} KB")
                        st.write("**Content Preview:**")
                        preview = (
                            item["content"][:200] + "..."
                            if len(item["content"]) > 200
                            else item["content"]
                        )
                        st.text(preview)
            else:
                with st.container():
                    st.markdown("*No files uploaded yet*")

            st.divider()

            # File upload section
            st.write("**Upload New File:**")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=["pdf", "md", "markdown"],
                help="Upload PDF or Markdown files to add to the knowledge base",
            )

            if uploaded_file is not None:
                # Optional title input
                custom_title = st.text_input(
                    "Custom title (optional)", value="", placeholder=uploaded_file.name
                )

                if st.button("Upload and Process", type="primary"):
                    with st.spinner("Processing file..."):
                        try:
                            response = upload_knowledge_file(
                                uploaded_file,
                                title=custom_title if custom_title else None,
                                destination_id=destination["id"],
                            )

                            if response.status_code == 200:
                                result = response.json()
                                st.success("✅ File processed successfully!")
                                st.info(
                                    f"Created {result['chunks_created']} text chunks for search"
                                )
                                st.rerun()  # Refresh the page to show new file
                            else:
                                error_detail = response.json().get(
                                    "detail", "Unknown error"
                                )
                                st.error(f"❌ Upload failed: {error_detail}")
                        except Exception as e:
                            st.error(f"❌ Error uploading file: {str(e)}")

            st.divider()

            # Knowledge search section
            st.write("**Search Knowledge Base:**")
            search_query = st.text_input("Search for information...")

            if search_query and st.button("Search", type="secondary"):
                with st.spinner("Searching..."):
                    try:
                        search_results = search_knowledge_base(
                            search_query, destination_id=destination["id"]
                        )

                        if search_results and search_results.get("results"):
                            st.write(
                                f"**Found {len(search_results['results'])} relevant results:**"
                            )

                            for i, result in enumerate(search_results["results"], 1):
                                with st.expander(
                                    f"Result {i}: {result['knowledge_item_title']} (Similarity: {result['similarity']:.2f})",
                                    expanded=i == 1,
                                ):
                                    st.write(
                                        f"**Source:** {result['knowledge_item_title']}"
                                    )
                                    st.write(f"**Type:** {result['source_type']}")
                                    st.write(f"**Chunk:** {result['chunk_index']}")
                                    st.write("**Content:**")
                                    st.text(result["chunk_text"])
                        else:
                            st.info(
                                "No relevant results found. Try a different search query."
                            )
                    except Exception as e:
                        st.error(f"❌ Search failed: {str(e)}")
