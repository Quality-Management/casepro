# Generated by Django 2.2.8 on 2019-12-10 14:58

from django.db import migrations


SQL = """
----------------------------------------------------------------------
-- Trigger function to maintain label counts and message.has_labels
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION msgs_message_labels_on_change() RETURNS TRIGGER AS $$
DECLARE
  _row msgs_message_labels;
  _message msgs_message;
  _remaing_label_id INT;
  _inbox_delta INT;
  _archived_delta INT;
BEGIN
  -- get the row being added/deleted and associated message
  IF TG_OP = 'INSERT' THEN _row := NEW; ELSE _row := OLD; END IF;
  SELECT * INTO STRICT _message FROM msgs_message WHERE id = _row.message_id;

  -- label applied to message
  IF TG_OP = 'INSERT' THEN
    UPDATE msgs_message SET has_labels = TRUE WHERE id = _row.message_id AND has_labels = FALSE;

    _inbox_delta := CASE WHEN msgs_is_inbox(_message) THEN 1 ELSE 0 END;
    _archived_delta := CASE WHEN msgs_is_archived(_message) THEN 1 ELSE 0 END;

  -- label removed from message
  ELSIF TG_OP = 'DELETE' THEN
    -- are there any remaining labels on this message?
    SELECT label_id INTO _remaing_label_id FROM msgs_message_labels WHERE message_id = _row.message_id LIMIT 1;
    IF NOT FOUND THEN
      UPDATE msgs_message SET has_labels = FALSE WHERE id = _row.message_id;
    END IF;

    _inbox_delta := CASE WHEN msgs_is_inbox(_message) THEN -1 ELSE 0 END;
    _archived_delta := CASE WHEN msgs_is_archived(_message) THEN -1 ELSE 0 END;
  END IF;

  IF _inbox_delta != 0 THEN
    INSERT INTO statistics_totalcount("item_type", "scope", "count", "is_squashed") VALUES('N', 'label:' || _row.label_id, _inbox_delta, FALSE);
  END IF;

  IF _archived_delta != 0 THEN
    INSERT INTO statistics_totalcount("item_type", "scope", "count", "is_squashed") VALUES('A', 'label:' || _row.label_id, _archived_delta, FALSE);
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

----------------------------------------------------------------------
-- Trigger function to maintain label counts
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION msgs_message_on_change() RETURNS TRIGGER AS $$
DECLARE
  _inbox_delta INT;
  _archived_delta INT;
BEGIN
  IF TG_OP = 'UPDATE' THEN

    IF NOT msgs_is_inbox(OLD) AND msgs_is_inbox(NEW) THEN
      _inbox_delta := 1;
    ELSIF msgs_is_inbox(OLD) AND NOT msgs_is_inbox(NEW) THEN
      _inbox_delta := -1;
    ELSE
      _inbox_delta := 0;
    END IF;

    IF NOT msgs_is_archived(OLD) AND msgs_is_archived(NEW) THEN
      _archived_delta := 1;
    ELSIF msgs_is_archived(OLD) AND NOT msgs_is_archived(NEW) THEN
      _archived_delta := -1;
    ELSE
      _archived_delta := 0;
    END IF;

    IF _inbox_delta != 0 THEN
      INSERT INTO statistics_totalcount("item_type", "scope", "count", "is_squashed")
      SELECT 'N', 'label:' || label_id, _inbox_delta, FALSE FROM msgs_message_labels WHERE message_id = NEW.id;
    END IF;

    IF _archived_delta != 0 THEN
      INSERT INTO statistics_totalcount("item_type", "scope", "count", "is_squashed")
      SELECT 'A', 'label:' || label_id, _archived_delta, FALSE FROM msgs_message_labels WHERE message_id = NEW.id;
    END IF;

  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("msgs", "0060_auto_20180814_2109"),
    ]

    operations = [migrations.RunSQL(SQL)]