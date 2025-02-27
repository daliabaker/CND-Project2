import os
import google.generativeai as genai
import json

genai.configure(api_key=os.environ['GEMINI_API'])

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
#   generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

PROMPT = "Generate a short title and a description for this image. Respond strictly in JSON format with 'title' and 'description' fields."

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  # print(file)
  return file

response = model.generate_content(
    [upload_to_gemini('licensed-image.jpeg', mime_type="image/jpeg"), "\n\n", PROMPT]
)

# print(response)
print(response.text)