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

# --- HTML templates ---
FORM_STAGE1 = """
<!DOCTYPE html>
<html>
<head>
    <title>Choose Subreddit</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; }
        input, button { width: 100%; margin: 10px 0; padding: 8px; }
    </style>
</head>
<body>
    <h2>Step 1: Enter Subreddit</h2>
    <form method="POST">
        <input type="text" name="subreddit" placeholder="Subreddit (without r/)" required>
        <button type="submit">Next</button>
    </form>
</body>
</html>
"""

FORM_STAGE2 = """
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
    <h2>Step 2: Create Post in r/{{subreddit}}</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="hidden" name="subreddit" value="{{subreddit}}">

        <label>Title</label>
        <input type="text" name="title" required>

        <label>Description (optional)</label>
        <textarea name="body"></textarea>

        <label>Flair (optional)</label>
        <select name="flair">
            <option value="">-- No Flair --</option>
            {% for flair in flairs %}
                <option value="{{flair['id']}}">{{flair['text']}}</option>
            {% endfor %}
        </select>

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
        # Stage 1 → Ask for subreddit and show flairs
        if "title" not in request.form:
            subreddit_name = request.form["subreddit"]
            flairs = list(reddit.subreddit(subreddit_name).flair.link_templates)
            return render_template_string(FORM_STAGE2, subreddit=subreddit_name, flairs=flairs)

        # Stage 2 → Actually submit the post
        subreddit_name = request.form["subreddit"]
        title = request.form["title"]
        body = request.form.get("body", "")
        flair_id = request.form.get("flair", "")
        pin_choice = "pin" in request.form

        # Save uploaded file
        image = request.files["image"]
        image_path = os.path.join("/tmp", image.filename)
        image.save(image_path)

        # Submit post
        subreddit = reddit.subreddit(subreddit_name)
        submission = subreddit.submit_image(title=title, image_path=image_path, flair_id=flair_id or None)

        # Add description as comment if provided
        if body.strip():
            submission.reply(body)

        # Pin to profile if chosen
        if pin_choice:
            submission.mod.sticky(state=True, bottom=False)

        return f"<p>✅ Posted: <a href='https://reddit.com{submission.permalink}' target='_blank'>View Post</a></p>"

    return FORM_STAGE1


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
