# singapore-parliament-speeches-streamlit

streamlit frontend for singapore-parliament-speeches

## To contribute

Install dependencies
```shell
pip install -r requirements.txt
```

Create filter with the relative path `.streamlit/secrets.toml`, contents:

> [!NOTE]
> These should be the credentials for the service account for `singapore-parliament-speeches`.
> Note that whenever deploying to the Cloud, these credentials must be copied.
```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "gbq-automate@singapore-parliament-speeches.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

Run streamlit:
>[!NOTE]
> In this case, `Singapore_Parliament_Speeches.py` is referred to because it is the first page.
```shell
streamlit run Singapore_Parliament_Speeches.py
```
