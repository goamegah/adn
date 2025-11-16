resource "google_bigquery_dataset" "feedback_dataset" {
  project       = var.dev_project_id
  dataset_id    = replace("${var.project_name}_feedback", "-", "_")
  friendly_name = "${var.project_name}_feedback"
  location      = var.region
  depends_on    = [resource.google_project_service.services]
}

resource "google_bigquery_dataset" "telemetry_logs_dataset" {
  project       = var.dev_project_id
  dataset_id    = replace("${var.project_name}_telemetry", "-", "_")
  friendly_name = "${var.project_name}_telemetry"
  location      = var.region
  depends_on    = [resource.google_project_service.services]
}

resource "google_logging_project_sink" "feedback_export_to_bigquery" {
  name        = "${var.project_name}_feedback"
  project     = var.dev_project_id
  destination = "bigquery.googleapis.com/projects/${var.dev_project_id}/datasets/${google_bigquery_dataset.feedback_dataset.dataset_id}"
  filter      = var.feedback_logs_filter

  bigquery_options {
    use_partitioned_tables = true
  }

  unique_writer_identity = true
  depends_on             = [google_bigquery_dataset.feedback_dataset]
}

resource "google_logging_project_sink" "log_export_to_bigquery" {
  name        = "${var.project_name}_telemetry"
  project     = var.dev_project_id
  destination = "bigquery.googleapis.com/projects/${var.dev_project_id}/datasets/${google_bigquery_dataset.telemetry_logs_dataset.dataset_id}"
  filter      = var.telemetry_logs_filter

  bigquery_options {
    use_partitioned_tables = true
  }

  unique_writer_identity = true
  depends_on             = [google_bigquery_dataset.telemetry_logs_dataset]
}

resource "google_project_iam_member" "bigquery_data_editor" {
  project = var.dev_project_id
  role    = "roles/bigquery.dataEditor"
  member  = google_logging_project_sink.log_export_to_bigquery.writer_identity
}

resource "google_project_iam_member" "feedback_bigquery_data_editor" {
  project = var.dev_project_id
  role    = "roles/bigquery.dataEditor"
  member  = google_logging_project_sink.feedback_export_to_bigquery.writer_identity
}
