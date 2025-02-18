import os
import logging
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import MedicalImage
from .utils import analyze_image_claude, get_image_features, generate_diagnosis_with_gpt_neo

# Set up logging
logger = logging.getLogger(__name__)

def index(request):
    """Render the homepage."""
    return render(request, 'index.html')

def upload(request):
    """Render the image upload page."""
    return render(request, 'upload.html')

def upload_image(request):
    """Handle image upload and processing."""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Get the uploaded image
            image = request.FILES['image']

            # Validate image size (e.g., 10 MB limit)
            if image.size > 10 * 1024 * 1024:  # 10 MB limit
                logger.error("Image size exceeds limit: %s", image.size)
                return render(request, 'upload.html', {'error': 'Image size exceeds the limit (10 MB).'})

            # Save the uploaded image
            image_path = default_storage.save(image.name, image)
            full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)
            logger.info("Image uploaded successfully: %s", full_image_path)

            # Analyze image using Claude API (with retries)
            diagnosis_claude = None
            retries = 3  # Retry API requests up to 3 times
            for attempt in range(retries):
                try:
                    diagnosis_claude = analyze_image_claude(full_image_path)
                    break
                except Exception as e:
                    logger.warning(f"Claude API attempt {attempt + 1} failed: {e}")
                    if attempt == retries - 1:
                        logger.error("Claude API request failed after retries.")
                        return render(request, 'upload.html', {'error': 'Failed to analyze the image. Please try again.'})

            # Extract image features
            image_features = get_image_features(full_image_path)
            if image_features is None:
                logger.error("Failed to extract image features: %s", full_image_path)
                return render(request, 'upload.html', {'error': 'Failed to process the image.'})

            # Generate diagnosis using GPT-Neo
            diagnosis_gpt_neo = generate_diagnosis_with_gpt_neo(image_features)
            final_diagnosis = f"{diagnosis_claude} | GPT-Neo Diagnosis: {diagnosis_gpt_neo}"

            # Save the result to the database
            medical_image = MedicalImage.objects.create(image=image, diagnosis=final_diagnosis)
            logger.info("Diagnosis saved: %s", final_diagnosis)

            # Redirect to the result page
            return redirect('result', pk=medical_image.pk)

        except Exception as e:
            logger.error("Error during image upload or analysis: %s", e, exc_info=True)
            return render(request, 'upload.html', {'error': 'An error occurred during image upload or analysis.'})

    # If not a POST request or no image uploaded, render the upload page
    return render(request, 'upload.html')

def result(request, pk):
    """Display the final diagnosis result."""
    try:
        # Fetch the MedicalImage instance
        medical_image = get_object_or_404(MedicalImage, pk=pk)
        return render(request, 'results.html', {'image': medical_image})
    except Exception as e:
        logger.error("Error fetching result: %s", e, exc_info=True)
        return render(request, 'results.html', {'error': 'An error occurred while fetching the result.'})