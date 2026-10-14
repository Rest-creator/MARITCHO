/// The kinds of work a worker can do offline and send later.
abstract final class OutboxActions {
  /// "I've arrived": the price confirmed on site.
  /// Payload: `job_id`, `labor_amount`, `materials_amount`.
  /// Sent as `POST /jobs/{job_id}/quote`.
  static const String submitQuote = 'SUBMIT_QUOTE';

  /// A photo of the work, shared in the job's chat.
  /// Payload: `job_id`, `file_path`, `upload_key`, and `media_url` once
  /// uploaded. Sent as `POST /media` (issue #1), then
  /// `POST /jobs/{job_id}/messages` with `message_type: PHOTO`.
  static const String sendPhoto = 'SEND_PHOTO';
}
