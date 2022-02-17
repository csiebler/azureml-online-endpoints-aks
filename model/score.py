import uuid
import os
import pandas as pd
import joblib
from inference_schema.schema_decorators import input_schema, output_schema
from inference_schema.parameter_types.standard_py_parameter_type import StandardPythonParameterType
from azure.identity import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential
from azure.storage.blob import BlobClient


endpoint = "https://<your blob account>.blob.core.windows.net"
credential = ChainedTokenCredential(ManagedIdentityCredential(), AzureCliCredential())

# Automatically generate the swagger interface by providing an data example
input_sample = [{
    "Age": 20,
    "Sex": "male",
    "Job": 0,
    "Housing": "own",
    "Saving accounts": "little",
    "Checking account": "little",
    "Credit amount": 100,
    "Duration": 48,
    "Purpose": "radio/TV"
  }]
output_sample = [[0.7, 0.3]]

def init():
    # Load model
    global model
    model_dir = os.getenv('AZUREML_MODEL_DIR')
    model_path = os.path.join(model_dir, 'credit-prediction.pkl')
    model = joblib.load(model_path)

@input_schema('data', StandardPythonParameterType(input_sample))
@output_schema(StandardPythonParameterType(output_sample))
def run(data):
    try:
        # Predict
        df = pd.DataFrame(data)
        proba = model.predict_proba(df)
        result = {"predict_proba": proba.tolist()}

        # This code is probably bad, as we do not want to get a new token every time - do not use this in production
        try:
            blob_client = BlobClient(endpoint, container_name="moe-testing", blob_name=f"{str(uuid.uuid4())}.txt", credential=credential)
            data = str(result)
            blob_client.upload_blob(data)
        except:
            print("Not able to write to Storage")

        return result
    except Exception as e:
        error = str(e)
        return error
