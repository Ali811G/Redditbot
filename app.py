import os
import praw
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- Reddit authentication ---
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("USER_AGENT")
)

# --- HTML form with drag & drop ---
HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Reddit Bot Post</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; }
        input, textarea, select, button { width: 100%; margin: 10px 0; padding: 8px; }
        .upload-box {
            border: 2px dashed #aaa;
            padding: 30px;
            text-align: center;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h2>Post to Reddit</h2>
    <form method="POST" enctype="multipart/form-data">
        <label>Subreddit</label>
        <input type="text" name="subreddit" required>

        <label>Title</label>
        <input type="text" name="title" required>

        <label>Description (optional)</label>
        <textarea name="body"></textarea>

        <label>Upload Image</label>
        <div class="upload-box" onclick="document.getElementById('file').click()">
            Drag & Drop or Click to Upload
        </div>
        <input type="file" id="file" name="image" style="display:none;" accept="image/*" required>

        <label><input type="checkbox" name="pin"> Pin this post to profile</label>

        <button type="submit">Submit to Reddit</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        subreddit_name = request.form["subreddit"]
        title = request.form["title"]
        body = request.form.get("body", "")
        pin_choice = "pin" in request.form

        # Save uploaded file
        image = request.files["image"]
        image_path = os.path.join("/tmp", image.filename)
        image.save(image_path)

        # Post to Reddit
        subreddit = reddit.subreddit(subreddit_name)
        submission = subreddit.submit_image(title=title, image_path=image_path)

        # Add description as comment if given
        if body.strip():
            comment = submission.reply(body)
            print("Added description as comment:", comment.id)

        # Pin to profile if chosen
        if pin_choice:
            submission.mod.sticky(state=True, bottom=False)

        return f"<p>✅ Posted: <a href='https://reddit.com{submission.permalink}' target='_blank'>View Post</a></p>"

    return render_template_string(HTML_FORM)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
