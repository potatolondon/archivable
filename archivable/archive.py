from django.db import models
from django.dispatch import Signal
from django.forms import ModelForm


def _add_field_to_class(cls, name):
    try:
        pk_field = next(x for x in cls._meta.fields if x.primary_key)
        pk_type = pk_field.__class__
    except StopIteration:
        pk_type = None

    if pk_type is None:
        pk_type = models.AutoField

    if pk_type == models.CharField:
        models.CharField(
            editable=False,
            max_length=pk_field.max_length,
            blank=True,
            default=""
        ).contribute_to_class(cls, name)
    else:
        models.BigIntegerField(
            editable=False,
            blank=True,
            default=0
        ).contribute_to_class(cls, name)


def _add_field_to_unique_constraints(cls, name):
    new_unique_togethers = []

    for field in cls._meta.fields:
        if field.unique and not field.primary_key:
            field._unique = False

            new_unique_togethers.append((field.name, "archive_identifier"))

    for constraint in cls._meta.unique_together:
        new_unique_togethers.append(
            tuple(list(constraint) + ["archive_identifier"])
        )

    cls._meta.unique_together = new_unique_togethers


def _replace_manager(cls, new_manager_name):
    if hasattr(cls, "objects"):
        default_manager = cls.objects.__class__
    else:
        default_manager = models.Manager

    class ExcludeArchivedManager(default_manager):
        use_in_migrations = False

        def get_queryset(self):
            return super(ExcludeArchivedManager, self).get_queryset().filter(archive_identifier=0)

    default_manager().contribute_to_class(cls, "with_archived")

    manager = ExcludeArchivedManager()
    manager.model = cls
    cls.objects = manager

    try:
        cls._default_manager = cls.objects
    except AttributeError:  # Django >= 1.10
        cls._meta.default_manager_name = cls.objects.name


post_archive = Signal(providing_args=["instance"])


def _override_methods(cls):

    class Mixin(object):
        def archive(self):
            self.archive_identifier = self.pk
            self.save(update_fields=["archive_identifier"])

            parent = super(Mixin, self)
            if hasattr(parent, "archive"):
                parent.archive()

            post_archive.send(sender=self.__class__, instance=self)

        def restore(self):
            self.archive_identifier = 0
            self.save(update_fields=["archive_identifier"])

            parent = super(Mixin, self)
            if hasattr(parent, "restore"):
                parent.restore()

        def delete(self, force=False, *args, **kwargs):
            if force:
                return super(Mixin, self).delete(*args, **kwargs)
            else:
                self.archive()

        @property
        def is_archived(self):
            return self.archive_identifier != 0

    # Insert our mixin above the class we are decorating in the __bases__
    cls.__bases__ = tuple([Mixin] + list(cls.__bases__))


def archivable(cls):
    """
        A class decorator that makes a model archivable

        Works by:

         - Adding an archive_identifier field, which if zero means the object is unarchived, otherwise
           it's made equal to the instance's PK
         - Manipulates unique constraints to add the archive_identifier
         - Overrides delete to instead archive unless you pass force=True as a param
         - Adds with_archived as a manager
         - Replaces objects with ExcludeArchivedManager
    """

    _add_field_to_class(cls, "archive_identifier")
    _add_field_to_unique_constraints(cls, "archive_identifier")
    _replace_manager(cls, "with_archived")
    _override_methods(cls)

    return cls


class ArchivableModelForm(ModelForm):
    def _get_validation_exclusions(self):
        """ `archive_identifier` is uneditable, so isn't validated, but is
        used in `unique_together` constraints. We remove it from the validation
        exclusion list to make sure it is validated when checking uniqueness.
        """
        excluded = super(BaseModelForm, self)._get_validation_exclusions()
        excluded.remove("archive_identifier")
