# EECE590X
Question Development for the EECE351 Digital Systems Design course at Binghamton University

## How it Works
Each question has an associated Python script, which generates relevant data to the question. This includes the question text, answers, hints, feedback, images, etc.

Dr. Summerville's `d2l` library is used to form a CSV file using the data in the question. Often, multiple variations of the same question are generated, making the CSV a question pool.

We can then upload the CSV file to Brightspace to import the questions and add them into the quizzes.

## Uploading Question Pools to Brightspace

Once the CSV question pools (and supplemental images) have been generated, you can turn them into Brightspace quizzes with the following steps:

### Upload Images to the File System
**If your questions have images attached, it is important to upload the images _before_ uploading questions, because otherwise the questions won't link the images properly.**
- Go to `Course Tools` -> `Course Admin` -> `Manage Files`
- Navigate to the image directory specified by the CSV / Python script (usually `/imagepools/alivebeef` or `/imagepools/quantumbeef`)
- `Upload`, select/drag the image, and finish with `Save`

#### Uploading Images in Mass
For convenience, there is a script to extract all images from a specified range of problem sets. Here is how to use it:
- Open a terminal in `EECE590X`
- `python3 extract_images.py <problem set numbers>`
- For example, `python3 extract_images.py 18-20 22` takes all images from problem sets 18, 19, 20, and 22

The images will be copied to `EECE590X/temp_images` where you can then upload all of them to Brightspace at once.

### Upload Questions to the Question Library
- Go to `Quizzes` -> `Question Library`
- Make a `New` -> `Section` (basically a folder)
- Name the section/folder something relevant, for example, `q14_6` for HW/Quiz 14 Question 6
- Navigate to the section/folder you just made
- `Import` -> `Upload File`
- Select/drag the CSV and finish with `Import All`

#### Extracting Question Pools in Mass
Similar to the script for images, there is a script to extract all images from a specified range of problem sets. Here is how to use it:
- Open a terminal in `EECE590X`
- `python3 extract_pools.py <problem set numbers>`
- For example, `python3 extract_pools.py 18-20 22` takes all pools from problem sets 18, 19, 20, and 22

The CSVs will be copied to `EECE590X/temp_pools` where you can then upload them to multiple Brightspace sections without having to navigate between different folders on your computer.

### Import Questions to a Quiz
- In the `Quizzes` tab, click on a quiz to edit it (or make a new quiz)
- `Create New` -> `Question Pool` -> `Browse Question Library`
- Select the section/folder with all the questions and `Import`
- Give the question pool a relevant name
- Select `1` for `Number of Questions to Select` (unless you want more)
- `Save` the question
- Be sure to `Preview` the quiz to make sure it looks right

## Setting Up for Development
In order to run the scripts, you may need to do some extra setup on your computer.

### Configuring Custom Libraries
This project uses many custom modules stored in the `libs` folder, the most notable being `d2l`. In order to use these modules in your Python files, you will need to add `libs` to your default Python path. Here's how to do this in Windows:
- Search the Start menu for "environment variables"
- Click `Environment Variables`
- Click `New` under `User Variables`
- Name the variable `PYTHONPATH` and make its value something like `C:/path/to/your/EECE590X/libs`
- Do the same for `System Variables`
- Confirm that it worked by going into a Python shell and entering `import sys; sys.path`
- Restart your command line / IDE if necessary

Alternatively, you can specify PYTHONPATH in the command line as you run the script:
- `PYTHONPATH="/path/to/your/EECE590X/libs" python3 <script>.py`

### Installing Inkscape
Inkscape is the backend this project currently uses for converting SVG to PNG. Similarly to the custom libraries, this will need to be installed and specified in your default path. Here's the list of steps for Windows:
- Download and install [Inkscape](https://inkscape.org/) (Latest stable version is fine)
- Search the Start menu for "environment variables"
- Click `Environment Variables`
- Find `PATH` under `System Variables` and click `Edit`
- Add a `New` value
- Enter your path to your Inkscape installation, such as `C:\Program Files\Inkscape\bin`

### Generating Requirements File
- `pip3 install pipreqs`
- `pipreqs . --force`

### Installing Requirements
- `pip3 install -r requirements.txt`

## Credits
LogicDesigner, FSM Explorer, and the `d2l` library were all made by Dr. Douglas Summerville, who is supervising question development.

The previous class homeworks, EECE251, has been stored for book keeping and reference if needed.
