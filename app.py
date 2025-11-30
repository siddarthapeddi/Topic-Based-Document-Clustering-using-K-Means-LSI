from flask import Flask, request, jsonify, send_from_directory
from maincode import run_document_clustering
from file_handler import process_uploaded_files, get_supported_formats
import logging

app = Flask(__name__, static_folder='.')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure file upload
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
UPLOAD_FOLDER = 'uploads'

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/supported-formats", methods=["GET"])
def get_formats():
    """Get list of supported file formats"""
    formats = get_supported_formats()
    return jsonify(formats)

@app.route("/cluster", methods=["POST"])
def cluster_api():
    try:
        # Check if we have file uploads
        if 'files' in request.files and len(request.files.getlist('files')) > 0:
            files = request.files.getlist('files')
            documents, errors = process_uploaded_files(files)
            
            if errors:
                logger.warning(f"File processing warnings: {errors}")
            
            if not documents:
                return jsonify({"error": f"No documents extracted. Errors: {'; '.join(errors)}"}), 400
            
            logger.info(f"Extracted {len(documents)} documents from {len(files)} files")
        
        # Also check for JSON text input
        elif request.is_json:
            data = request.get_json(silent=True)
            
            if not data:
                return jsonify({"error": "No JSON received"}), 400

            documents = data.get("documents", [])
            
            # INPUT VALIDATION
            if not documents or len(documents) == 0:
                return jsonify({"error": "Please enter at least one document"}), 400
            
            # Filter empty documents
            documents = [d.strip() for d in documents if d.strip()]
            
            if len(documents) == 0:
                return jsonify({"error": "No valid documents found"}), 400
        else:
            return jsonify({"error": "Please provide either documents or files"}), 400

        k = int(request.form.get('clusters', request.get_json(silent=True).get('clusters', 2) if request.is_json else 2))

        if k < 2 or k > 20:
            return jsonify({"error": "Number of clusters must be between 2 and 20"}), 400
        
        if len(documents) < k:
            return jsonify({"error": f"Number of clusters ({k}) cannot exceed number of documents ({len(documents)})"}), 400

        logger.info(f"Clustering {len(documents)} documents into {k} clusters")
        
        # RUN THE CLUSTERING
        labels, topics, clusters_dict = run_document_clustering(documents, k)
        logger.info("Clustering completed successfully")
        
        return jsonify({"clusters": clusters_dict, "success": True})
    
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Clustering failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
