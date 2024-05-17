from flask import Flask, render_template, send_from_directory, redirect, url_for, Response, send_file
from application_forms import UploadFileForm, ChooseOperationForm, ChooseOperationsForm, DownloadProcessedImageForm, DownloadProcessedImagesForm
from werkzeug.utils import secure_filename
import os
from PIL import Image
from remote_procedure_calls import process_images
import zipfile

# Create flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mofta7_sery'    
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/images/')

#############################################################################################

# Global Variables

# Create an array of uploaded files
uploaded_files = []
# Message to be sent to server
msg = []
# Processed images
zipped_processed_images = []

#############################################################################################


# Define home function, allows user to upload images
@app.route('/', methods= ['GET', 'POST'])
@app.route('/home', methods= ['GET', 'POST'])
def home():

    # Create an upload form instance
    form = UploadFileForm()

    if form.validate_on_submit(): # What happens when we submit the form
            
            if form.upload.data:
            # Grab the file
                file = form.file.data 
                # Save the file
                file.save(
                    os.path.join(
                        os.path.abspath(os.path.dirname(__file__)),         # Application root directory
                        app.config['UPLOAD_FOLDER'],                # Upload folder path
                        secure_filename(file.filename)              # Secure file to be saved
                    ))
                # Update uploaded files array
                uploaded_files.append(file.filename)
                # Update the view
                return render_template('upload_page.html', form= form, filenames = uploaded_files)
            if form.next.data:
                # Return a page allowing user to choose the image and the operation required with it
                # return redirect(url_for('choose_operation', filename= secure_filename(file.filename)))
                return redirect('choose_operations')
    

    # Return upload page and the form
    return render_template('upload_page.html', form= form)

#############################################################################################

# Get the constructed form to be displatyed to the user
@app.route('/choose_operations', methods=['GET'])
def choose_operations_get():
     
    # Create a form to submit multiple operations for multiple images
    form = ChooseOperationsForm()

    # Fill in the Form data
    operations_data = [{'imageName': uploaded_img, 'operation': ChooseOperationForm()} for uploaded_img in uploaded_files]
    form.process(data={'operations': operations_data})

    # Return the Form
    return render_template('choose_operation.html', form=form)

# Post the filled form from the user
@app.route('/choose_operations', methods=['POST'])
def choose_operations_post():
     
    form = ChooseOperationsForm()

    # Construct the message
    global msg
    msg = [{'image': entry['imageName'], 'operation': entry['operation']} for entry in form.operations.data]
    zipped_processed_images = process_images(msg)

    # # Create folder for proccessed images
    # processed_folder = os.path.join(app.static_folder, 'processed_images')
    # if not os.path.exists(processed_folder):
    #     os.makedirs(processed_folder)

    # # # Save the processed image 
    # processed_file_path = os.path.join(processed_folder, 'zipped_processed_imgs')
    # zipped_processed_images.save(processed_file_path)

    
    # Redirect to 'loading' function
    return redirect('download_file')

#############################################################################################

# Define download function, allows user to download images
@app.route('/download_file', methods= ['POST', 'GET'])
def download_file():
    
    # Create an download form instance
    form = DownloadProcessedImageForm()
    
#    # print(f"################# {app.static_folder}")
    if form.validate_on_submit(): # What happens when we submit the form

        # Download the file
        # processed_folder = os.path.join(app.static_folder, 'processed_images')
        # processed_file_path = os.path.join(processed_folder, filename)
        # return send_file(path_or_file=processed_file_path, mimetype= 'image/jpg', as_attachment= True)
        try:
            return send_file(path_or_file = './static/processed_images/processed_images_zip.rar',
                             mimetype = 'application/zip',
                            as_attachment=True)
        except FileNotFoundError:
            return "error: couldn't download"
        
        
    # Return download page and the form
    return render_template('download_processed_image.html', form= form)
    

#############################################################################################

# Run the flask application
if __name__ == '__main__':
    app.run(debug=True)

