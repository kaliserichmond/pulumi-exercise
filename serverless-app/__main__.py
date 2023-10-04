from cProfile import run
from pip import main
import pulumi
import pulumi_gcp as gcp
import pulumi_synced_folder as synced
from pulumi_gcp import sql
# import sqlalchemy


class MyComponent(pulumi.ComponentResource):
    def __init__(self, name, opts = None):
        super().__init__('pkg:index:MyComponent', name, None, opts)
        self.bucket = gcp.storage.Bucket(
            "kr-pulumi-exercise",
            gcp.storage.BucketArgs(
                location="US",
            ),
            opts=pulumi.ResourceOptions(parent=self) 
        )
        self.database_instance = sql.DatabaseInstance("kr-db-instance", 
            database_version = "MYSQL_5_7",
            name = "kr-pulumi-exercise-db-instance",
            region = "us-central1",
            settings = {
                "tier": "db-f1-micro",
            },
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.database = gcp.sql.Database("kr-db", 
            instance="kr-db-instance",
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.register_outputs({
            'instance_connection_name': self.database_instance.connection_name,
            'kr_bucket_self_link': self.bucket.url,
            'kr_bucket_name':self.bucket.name
        })

exercise_component = MyComponent("exercise_component")

# Import the program's configuration settings.
config = pulumi.Config()
site_path = config.get("sitePath", "./www")
app_path = config.get("appPath", "./app")
index_document = config.get("indexDocument", "index.html")
error_document = config.get("errorDocument", "error.html")

# Create a storage bucket and configure it as a website.
site_bucket = gcp.storage.Bucket(
    "site-bucket",
    gcp.storage.BucketArgs(
        location="US",
        website=gcp.storage.BucketWebsiteArgs(
            main_page_suffix=index_document,
            not_found_page=error_document,
        ),
    ),
)

# Create an IAM binding to allow public read access to the bucket.
site_bucket_iam_binding = gcp.storage.BucketIAMBinding(
    "site-bucket-iam-binding",
    gcp.storage.BucketIAMBindingArgs(
        # bucket=site_bucket.name, role="roles/storage.objectViewer", members=["allUsers"]
        bucket=site_bucket.name, role="roles/storage.objectAdmin", members=["allUsers"]
    ),
)

# Use a synced folder to manage the files of the website.
synced_folder = synced.GoogleCloudFolder(
    "synced-folder",
    synced.GoogleCloudFolderArgs(
        path=site_path,
        bucket_name=site_bucket.name,
    ),
)

# Create another storage bucket for the serverless app.
app_bucket = gcp.storage.Bucket(
    "app-bucket",
    gcp.storage.BucketArgs(
        location="US",
    ),
)

# Upload the serverless app to the storage bucket.
app_archive = gcp.storage.BucketObject(
    "app-archive",
    gcp.storage.BucketObjectArgs(
        bucket=app_bucket.name,
        source=pulumi.asset.FileArchive(app_path),
    ),
)

# Create a Cloud Function that returns some data.
data_function = gcp.cloudfunctions.Function(
    "data-function",
    gcp.cloudfunctions.FunctionArgs(
        source_archive_bucket=app_bucket.name,
        source_archive_object=app_archive.name,
        runtime="python310",
        entry_point="data",
        trigger_http=True,
    ),
)

# # Cloud Function for putting data to the database
# function_source_code = """
# exports.handler = function(event, context, callback) {
#     callback();
# };
# """

# Create a cloud function when object lands in bucket
exercise_function = gcp.cloudfunctions.Function(
    "exercise_function",
    gcp.cloudfunctions.FunctionArgs(
        source_archive_bucket="kr_pulumi_exercise",
        source_archive_object="kr_pulumi_exercise",
        runtime="python310",
        entry_point="exercise_handler",
        event_trigger={
                "event_type": "google.cloud.storage.object.v1.finalized",
                "resource" : "projects/pulumi-exercise/storage/kr-pulumi-exercise"  
            },
    )
)

# Create an IAM member to invoke the function.
invoker = gcp.cloudfunctions.FunctionIamMember(
    "data-function-invoker",
    gcp.cloudfunctions.FunctionIamMemberArgs(
        project=data_function.project,
        region=data_function.region,
        cloud_function=data_function.name,
        role="roles/cloudfunctions.invoker",
        member="allUsers",
    ),
)
# Create an IAM member to invoke the function.
exercise_invoker = gcp.cloudfunctions.FunctionIamMember(
    "exercise-function-invoker",
    gcp.cloudfunctions.FunctionIamMemberArgs(
        project=exercise_function.project,
        region=exercise_function.region,
        cloud_function=exercise_function.name,
        role="roles/cloudfunctions.invoker",
        member="allUsers",
    ),
)

# Create a JSON configuration file for the website.
site_config = gcp.storage.BucketObject(
    "site-config",
    gcp.storage.BucketObjectArgs(
        name="config.json",
        bucket=site_bucket.name,
        content_type="application/json",
        source=data_function.https_trigger_url.apply(
            lambda url: pulumi.StringAsset('{ "api": "' + url + '" }')
        ),
    ),
)

# Export the URLs of the website and serverless endpoint.
pulumi.export(
    "siteURL",
    site_bucket.name.apply(
        lambda name: f"https://storage.googleapis.com/{name}/index.html"
    ),
)
pulumi.export("apiURL", data_function.https_trigger_url.apply(lambda url: url))


# possibly need to to the apply here? 
# pulumi.export("instanceConnectionName", exercise_component.instance_connection_name)
# pulumi.export("krBucketSelfLink", exercise_component.kr_bucket_self_link)
# pulumi.export("krBucketSelfLink", exercise_component.kr_bucket_name)