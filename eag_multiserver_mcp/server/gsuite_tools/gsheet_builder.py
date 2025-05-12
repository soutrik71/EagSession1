import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from dotenv import load_dotenv
import os
import time
import glob

load_dotenv()


def create_gsheet_from_json(
    json_path: str,
    credentials_path: str = "./server/credentials.json",
    email: str = None,
    sheet_prefix: str = "F1_Report",
    save_url_to_folder: str = "./server/outputs",
) -> str:
    """
    Create a Google Sheet from a JSON file and return the URL.

    Args:
        json_path: Path to the JSON file to load
        credentials_path: Path to the Google service account credentials
        email: Email to share the sheet with (uses EMAIL env var if None)
        sheet_prefix: Prefix for the sheet name
        save_url_to_folder: Folder to save the sheet URL to (None to skip saving)

    Returns:
        str: URL of the created Google Sheet
    """
    # --- Step 1: Check if the JSON file exists ---
    if not os.path.exists(json_path):
        # Try to find matching files in the directory
        base_dir = os.path.dirname(json_path)
        base_filename = os.path.basename(json_path)

        if not os.path.exists(base_dir):
            raise FileNotFoundError(f"Directory not found: {base_dir}")

        # Look for similar files
        similar_files = glob.glob(os.path.join(base_dir, "*.json"))
        if similar_files:
            similar_files_str = "\n- ".join(
                [""] + [os.path.basename(f) for f in similar_files]
            )
            raise FileNotFoundError(
                f"JSON file not found at {json_path}\n"
                f"Available JSON files in {base_dir}:{similar_files_str}"
            )
        else:
            raise FileNotFoundError(
                f"JSON file not found at {json_path}\n"
                f"No JSON files found in {base_dir}"
            )

    # Try to load and validate the JSON file
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {json_path}")

    # Check required fields in the JSON
    if "url_tables" not in data or not isinstance(data["url_tables"], list):
        raise ValueError(f"Missing or invalid 'url_tables' field in: {json_path}")

    # Use environment variable if email not provided
    if email is None:
        email = os.getenv("EMAIL")
        if not email and save_url_to_folder:
            print("WARNING: No email provided or set in EMAIL environment variable.")

    # --- Step 2: Setup Authentication ---
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    try:
        # Try to load the file to verify it's a valid JSON
        with open(credentials_path, "r") as f:
            creds_content = json.load(f)

        # Check if it has the right structure for a service account
        if (
            "type" not in creds_content
            or creds_content.get("type") != "service_account"
        ):
            raise ValueError(
                "Your credentials file is not a valid service account key file.\n"
                "Make sure to download the correct JSON key from Google Cloud Console.\n"
                "It should contain 'type': 'service_account' and proper credentials."
            )

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope
        )
        client = gspread.authorize(creds)

    except json.JSONDecodeError:
        raise ValueError("Your credentials file is not a valid JSON file.")
    except Exception as e:
        raise ConnectionError(f"Error connecting to Google Sheets API: {str(e)}")

    # --- Step 3: Create a new Google Sheet ---
    try:
        # Create sheet name (with or without timestamp)
        sheet_name = f"{sheet_prefix}"
        spreadsheet = client.create(sheet_name)

        # Share the sheet with the email
        if email:
            try:
                spreadsheet.share(email, perm_type="user", role="writer")
            except gspread.exceptions.APIError as e:
                if "exceeded your sharing quota" in str(e):
                    print(
                        "WARNING: Sharing quota exceeded. Sheet created but not shared."
                    )
                    print(f"You can manually access the sheet at: {spreadsheet.url}")
                else:
                    raise

        # --- Step 4: Add a summary sheet first ---
        worksheet = spreadsheet.add_worksheet(title="Summary", rows="5", cols="2")
        worksheet.update(
            [
                ["Query", data.get("query", "")],
                ["Timestamp", data.get("timestamp", "")],
                [
                    "Source URL",
                    data.get("result", {}).get("url", "") if "result" in data else "",
                ],
                ["Generated On", time.strftime("%Y-%m-%d %H:%M:%S")],
            ]
        )

        # --- Step 5: Add text content ---
        if "url_text" in data and data["url_text"]:
            # Split text into chunks to avoid cell size limits
            text_chunks = [
                data["url_text"][i : i + 50000]
                for i in range(0, len(data["url_text"]), 50000)
            ]

            text_worksheet = spreadsheet.add_worksheet(
                title="Text_Content", rows=str(len(text_chunks) + 1), cols="1"
            )
            cells = []
            for i, chunk in enumerate(text_chunks):
                cells.append([f"Part {i+1}"])
                cells.append([chunk])

            text_worksheet.update(cells)

        # --- Step 6: Add each table as a separate sheet ---
        if "url_tables" in data and isinstance(data["url_tables"], list):
            for idx, table_dict in enumerate(data["url_tables"]):
                sheet_title = f"Table_{idx + 1}"

                # Convert dict to DataFrame
                df = pd.DataFrame(table_dict)

                # Create worksheet with appropriate dimensions
                rows = len(df) + 1  # +1 for header
                cols = len(df.columns)

                # Add worksheet with minimum size to avoid errors
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_title, rows=str(max(rows, 10)), cols=str(max(cols, 5))
                )

                # Update worksheet with DataFrame content
                try:
                    worksheet.update([df.columns.tolist()] + df.values.tolist())
                    # Format header row (optional)
                    worksheet.format("1:1", {"textFormat": {"bold": True}})
                except Exception as e:
                    print(f"Error updating worksheet {sheet_title}: {str(e)}")

        # --- Step 7: Delete the default Sheet1 ---
        try:
            spreadsheet.del_worksheet(spreadsheet.sheet1)
        except Exception:
            pass  # Ignore if it doesn't exist or can't be deleted

        # --- Step 8: Save the URL to a file if requested ---
        if save_url_to_folder:
            os.makedirs(save_url_to_folder, exist_ok=True)

            # Create clean filename from the JSON path
            base_filename = os.path.basename(json_path).replace(".json", "")
            url_file_path = os.path.join(
                save_url_to_folder, f"gsheet_url_{base_filename}.txt"
            )

            with open(url_file_path, "w") as f:
                f.write(f"Google Sheet URL: {spreadsheet.url}\n")
                f.write(f"Created from: {json_path}\n")
                f.write(f"Created on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Created by: {email}\n")
                f.write(f"Query: {data.get('query', '')}\n")

            print(f"Sheet URL saved to: {url_file_path}")

        return spreadsheet.url

    except gspread.exceptions.APIError as e:
        if "exceeded your sharing quota" in str(e):
            raise RuntimeError(
                "Google API sharing quota exceeded. "
                "You may have created too many sheets or shared too many documents recently. "
                "Wait a few hours and try again, or use a different service account."
            )
        else:
            raise RuntimeError(f"Google Sheets API error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error creating Google Sheet: {str(e)}")


# Example usage when run as a script
if __name__ == "__main__":
    try:
        # Get the JSON file path from command line args or use default
        import sys

        json_path = (
            sys.argv[1]
            if len(sys.argv) > 1
            else "./server/outputs/formula_1_2025_driver_standings.json"
        )

        # Create the Google Sheet
        sheet_url = create_gsheet_from_json(json_path)

        print(f"Google Sheet created successfully: {sheet_url}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        exit(1)
