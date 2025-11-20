"""
LEGO Brick Workflow Interpreter
A FastAPI web service that detects LEGO bricks from images and converts them to workflow graphs.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Tuple
from dataclasses import dataclass
from PIL import Image
import cv2
import numpy as np
import io

app = FastAPI(title="LEGO Workflow Interpreter")

# ==================== Data Models ====================

@dataclass
class Brick:
    """Represents a detected LEGO brick."""
    id: str
    color: str
    x: float
    y: float

class Node(BaseModel):
    """Workflow graph node."""
    id: str
    type: str

class WorkflowGraph(BaseModel):
    """Complete workflow graph with nodes and edges."""
    nodes: List[Node]
    edges: List[Tuple[str, str]]

# ==================== Constants ====================

COLOR_TO_TYPE = {
    "green": "Start",
    "blue": "Action",
    "yellow": "Decision",
    "red": "End",
}

# HSV color ranges for brick detection
# Format: (lower_bound, upper_bound) in HSV space
HSV_RANGES = {
    "green": (np.array([35, 50, 50]), np.array([85, 255, 255])),
    "blue": (np.array([90, 50, 50]), np.array([130, 255, 255])),
    "yellow": (np.array([20, 100, 100]), np.array([35, 255, 255])),
    "red": (
        # Red wraps around the hue circle, so we need two ranges
        [(np.array([0, 50, 50]), np.array([10, 255, 255])),
         (np.array([170, 50, 50]), np.array([180, 255, 255]))]
    ),
}

# ==================== Brick Detection ====================

def detect_bricks_from_image(img: Image.Image) -> List[Brick]:
    """
    Detect LEGO bricks from an image using simple color-based detection.
    
    Args:
        img: PIL Image object
        
    Returns:
        List of detected Brick objects with id, color, x, y
    """
    # Convert PIL Image to OpenCV format
    img_array = np.array(img)
    if len(img_array.shape) == 2:  # Grayscale
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
    elif img_array.shape[2] == 4:  # RGBA
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
    else:  # RGB
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Convert to HSV for better color detection
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    
    bricks = []
    brick_counter = 1
    
    for color_name, hsv_range in HSV_RANGES.items():
        # Handle red's special case (wraps around hue circle)
        if color_name == "red":
            mask1 = cv2.inRange(img_hsv, hsv_range[0][0], hsv_range[0][1])
            mask2 = cv2.inRange(img_hsv, hsv_range[1][0], hsv_range[1][1])
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(img_hsv, hsv_range[0], hsv_range[1])
        
        # Apply morphological operations to reduce noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Filter by area to ignore noise
            area = cv2.contourArea(contour)
            if area < 100:  # Minimum area threshold
                continue
            
            # Calculate centroid
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
            
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            
            brick = Brick(
                id=f"b{brick_counter}",
                color=color_name,
                x=cx,
                y=cy
            )
            bricks.append(brick)
            brick_counter += 1
    
    return bricks

# ==================== Workflow Logic ====================

def bricks_to_workflow(bricks: List[Brick]) -> WorkflowGraph:
    """
    Convert detected bricks to a workflow graph.
    
    Args:
        bricks: List of detected Brick objects
        
    Returns:
        WorkflowGraph with nodes and edges
        
    Raises:
        ValueError: If workflow validation fails
    """
    # Filter bricks by valid colors
    valid_bricks = [b for b in bricks if b.color in COLOR_TO_TYPE]
    
    if not valid_bricks:
        raise ValueError("No interpretable bricks found")
    
    # Sort by x coordinate (left to right)
    sorted_bricks = sorted(valid_bricks, key=lambda b: b.x)
    
    # Create nodes
    nodes = [Node(id=brick.id, type=COLOR_TO_TYPE[brick.color]) for brick in sorted_bricks]
    
    # Validate: exactly one Start and one End
    start_nodes = [n for n in nodes if n.type == "Start"]
    end_nodes = [n for n in nodes if n.type == "End"]
    
    if len(start_nodes) == 0:
        raise ValueError("Workflow must have exactly one Start node (green brick)")
    if len(start_nodes) > 1:
        raise ValueError(f"Workflow has {len(start_nodes)} Start nodes, but must have exactly one")
    
    if len(end_nodes) == 0:
        raise ValueError("Workflow must have exactly one End node (red brick)")
    if len(end_nodes) > 1:
        raise ValueError(f"Workflow has {len(end_nodes)} End nodes, but must have exactly one")
    
    # Create edges (sequential connections)
    edges = []
    for i in range(len(sorted_bricks) - 1):
        edges.append((sorted_bricks[i].id, sorted_bricks[i + 1].id))
    
    return WorkflowGraph(nodes=nodes, edges=edges)

# ==================== API Endpoints ====================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve a simple HTML upload form."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LEGO Workflow Interpreter</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            .upload-form {
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 30px;
                text-align: center;
                margin: 20px 0;
            }
            input[type="file"] {
                margin: 20px 0;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #45a049;
            }
            .instructions {
                background-color: #f0f0f0;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
            }
            .color-guide {
                display: flex;
                justify-content: space-around;
                margin: 20px 0;
            }
            .color-item {
                text-align: center;
            }
            .color-box {
                width: 60px;
                height: 60px;
                margin: 0 auto 10px;
                border-radius: 4px;
                border: 2px solid #333;
            }
            .green { background-color: #4CAF50; }
            .blue { background-color: #2196F3; }
            .yellow { background-color: #FFEB3B; }
            .red { background-color: #F44336; }
        </style>
    </head>
    <body>
        <h1>🧱 LEGO Workflow Interpreter</h1>
        
        <div class="instructions">
            <h3>Instructions:</h3>
            <p>Upload a photo of LEGO bricks arranged left-to-right to create a workflow graph.</p>
            <p>The system will detect colored bricks and interpret them as workflow steps.</p>
        </div>
        
        <div class="color-guide">
            <div class="color-item">
                <div class="color-box green"></div>
                <strong>Green</strong><br>Start
            </div>
            <div class="color-item">
                <div class="color-box blue"></div>
                <strong>Blue</strong><br>Action
            </div>
            <div class="color-item">
                <div class="color-box yellow"></div>
                <strong>Yellow</strong><br>Decision
            </div>
            <div class="color-item">
                <div class="color-box red"></div>
                <strong>Red</strong><br>End
            </div>
        </div>
        
        <div class="upload-form">
            <h3>Upload Image</h3>
            <form action="/analyze-image" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept="image/*" required>
                <br>
                <button type="submit">Analyze Workflow</button>
            </form>
        </div>
        
        <div class="instructions">
            <h3>API Usage:</h3>
            <p><strong>POST /analyze-image</strong> - Upload an image file</p>
            <p>Returns JSON with workflow graph: nodes and edges</p>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze an uploaded image and return the detected workflow graph.
    
    Args:
        file: Uploaded image file
        
    Returns:
        JSON with workflow graph (nodes and edges)
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Detect bricks
        bricks = detect_bricks_from_image(image)
        
        if not bricks:
            raise HTTPException(
                status_code=400,
                detail="No bricks detected in image. Please ensure the image has clearly visible colored LEGO bricks."
            )
        
        # Convert to workflow
        try:
            workflow = bricks_to_workflow(bricks)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        return workflow
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )

# ==================== Example Usage ====================

def example_workflow():
    """Example showing how the workflow logic works with hardcoded bricks."""
    print("\n=== Example Workflow ===\n")
    
    # Create example bricks (simulating detected bricks in left-to-right order)
    example_bricks = [
        Brick(id="b1", color="green", x=100, y=200),
        Brick(id="b2", color="blue", x=250, y=200),
        Brick(id="b3", color="yellow", x=400, y=200),
        Brick(id="b4", color="blue", x=550, y=200),
        Brick(id="b5", color="red", x=700, y=200),
    ]
    
    print("Input bricks:")
    for brick in example_bricks:
        print(f"  {brick.id}: {brick.color} at ({brick.x}, {brick.y})")
    
    # Convert to workflow
    workflow = bricks_to_workflow(example_bricks)
    
    print("\nGenerated workflow:")
    print(f"Nodes: {workflow.nodes}")
    print(f"Edges: {workflow.edges}")
    print("\nJSON output:")
    print(workflow.model_dump_json(indent=2))

if __name__ == "__main__":
    # Run example
    example_workflow()
    
    # Instructions for running the server
    print("\n" + "="*50)
    print("To run the server:")
    print("  uvicorn main:app --reload")
    print("\nThen open: http://localhost:8000")
    print("="*50 + "\n")
