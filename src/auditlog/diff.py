from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model, NOT_PROVIDED
from django.utils.encoding import smart_text


def model_instance_diff(old, new, **kwargs):
    """
    Calculate the differences between two model instances. One of the instances may be None (i.e., a newly
    created model or deleted model). This will cause all fields with a value to have changed (from the fields default
    value).
    """
    from auditlog.registry import auditlog

    if not(old is None or isinstance(old, Model)):
        raise TypeError("The supplied old instance is not a valid model instance.")
    if not(new is None or isinstance(new, Model)):
        raise TypeError("The supplied new instance is not a valid model instance.")

    diff = {}

    if old is not None and new is not None:
        fields = set(old._meta.fields + new._meta.fields)
        model_fields = auditlog.get_model_fields(new._meta.model)
    elif old is not None:
        fields = set(old._meta.fields)
        model_fields = auditlog.get_model_fields(old._meta.model)
    elif new is not None:
        fields = set(new._meta.fields)
        model_fields = auditlog.get_model_fields(new._meta.model)
    else:
        fields = set()
        model_fields = None

    # Check if fields must be filtered
    if model_fields and (model_fields['include_fields'] or model_fields['exclude_fields']) and fields:
        filtered_fields = []
        if model_fields['include_fields']:
            filtered_fields = [field for field in fields
                               if field.name in model_fields['include_fields']]
        else:
            filtered_fields = fields
        if model_fields['exclude_fields']:
            filtered_fields = [field for field in filtered_fields
                               if field.name not in model_fields['exclude_fields']]
        fields = filtered_fields

    for field in fields:
        try:
            old_value = getattr(old, field.name, None)
        except ObjectDoesNotExist:
            old_value = field.default if field.default is not NOT_PROVIDED else None

        try:
            new_value = getattr(new, field.name, None)
        except ObjectDoesNotExist:
            new_value = None

        if old_value != new_value:
            diff[field.name] = (smart_text(old_value), smart_text(new_value))

    if len(diff) == 0:
        diff = None

    return diff
