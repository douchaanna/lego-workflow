# LEGO Workflow Interpreter

A FastAPI web service that interprets LEGO brick arrangements as workflow graphs.

## Features
- Upload photo of LEGO bricks
- Detects colors: Green (Start), Blue (Action), Yellow (Decision), Red (End)
- Returns workflow graph as JSON

## Deployment
Deployed on Render: [Add your URL here after deployment]
```
4. Click **"Commit new file"**

### Step 4: Verify Your Repository

Your repository should now show 3 files:
- `main.py`
- `requirements.txt`
- `README.md`

✅ **GitHub setup complete!**

---

## **Part 2: Deploy to Render**

### Step 1: Create Render Account

1. Go to https://render.com
2. Click **"Get Started"** or **"Sign Up"**
3. Choose **"Sign up with GitHub"** (this is easiest and connects automatically)
4. Authorize Render to access your GitHub account
5. Complete any additional signup steps

### Step 2: Create New Web Service

1. You should land on the Render Dashboard
2. Click the **"New +"** button in the top-right
3. Select **"Web Service"** from the dropdown

### Step 3: Connect Your Repository

1. You'll see a list of your GitHub repositories
2. Find **"lego-workflow"** in the list
3. Click **"Connect"** button next to it

**If you don't see your repository:**
- Click **"Configure account"** 
- Make sure Render has access to your repositories
- Return and refresh

### Step 4: Configure the Web Service

Now you'll see a configuration form. Fill it out exactly like this:

#### Basic Settings:
- **Name**: `lego-workflow` (or choose your own, must be unique)
- **Region**: Choose the closest to you (e.g., "Oregon (US West)" or "Frankfurt (EU)")
- **Branch**: `main` (should be auto-detected)
- **Root Directory**: Leave **blank**
- **Runtime**: **Python 3** (should be auto-detected)

#### Build & Deploy Settings:
- **Build Command**: 
```
  pip install -r requirements.txt
```
  (Should be auto-filled)

- **Start Command**: 
```
  uvicorn main:app --host 0.0.0.0 --port $PORT
```
  **⚠️ IMPORTANT**: Copy this exactly. The `$PORT` is crucial - Render provides this automatically.

#### Instance Type:
- Select **"Free"** plan
  - Note: Free instances spin down after 15 minutes of inactivity
  - First request after sleep takes ~30 seconds
  - Upgrade to paid ($7/mo) for always-on if needed

#### Advanced Settings (expand if needed):
- **Auto-Deploy**: **Yes** (recommended - deploys automatically when you push to GitHub)
- **Environment Variables**: None needed for this app
- Leave everything else as default

### Step 5: Deploy!

1. Scroll down and click **"Create Web Service"**
2. Render will start the deployment process

### Step 6: Watch the Build

You'll see a live log stream showing:
1. **Cloning repository** (10-20 seconds)
2. **Building** - Installing dependencies (2-4 minutes)
   - You'll see pip installing FastAPI, OpenCV, etc.
   - OpenCV takes the longest
3. **Starting service** (10-20 seconds)
4. **Status changes to "Live"** with a green dot ✅

**The entire process takes 3-5 minutes.**

### Step 7: Get Your Public URL

Once deployment is complete:
1. At the top of the page, you'll see your app's URL:
```
   https://lego-workflow-xxxx.onrender.com
