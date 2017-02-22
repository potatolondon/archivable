from django.db import models
from django.test import TestCase
import mock

from . import archivable
from .archive import _add_field_to_class, _replace_manager


@archivable
class ArchiveModel(models.Model):
    """The `archivable` decorator overrides methods, but we sometimes still want
    to check that the overriden method is called. To do this we call another
    method that isn't overriden, and can therefore be mocked.
    """

    name = models.CharField(max_length=100, unique=True)

    def delete(self, *args, **kwargs):
        self.overriden_delete(*args, **kwargs)

    def overriden_delete(self, *args, **kwargs):
        super(ArchiveModel, self).delete(*args, **kwargs)


class ArchiveTests(TestCase):

    @mock.patch.object(ArchiveModel, "save")
    def test_achive_sets_archive_identifier(self, mock_save):
        instance = ArchiveModel(name="one", pk=1)
        self.assertEqual(0, instance.archive_identifier)
        instance.archive()
        self.assertEqual(instance.pk, instance.archive_identifier)

    @mock.patch.object(ArchiveModel, "save")
    @mock.patch.object(ArchiveModel, "overriden_delete")
    def test_delete_archives(self, mock_overriden_delete, mock_save):
        instance = ArchiveModel(name="one", id=1, pk=1)
        instance.delete()
        self.assertEqual(instance.pk, instance.archive_identifier)
        self.assertEqual(mock_overriden_delete.call_count, 0)

    @mock.patch.object(ArchiveModel, "overriden_delete")
    def test_delete_deletes_with_force(self, mock_overriden_delete):
        instance = ArchiveModel(name="one", id=1, pk=1)
        instance.delete(force=True)
        self.assertNotEqual(instance.pk, instance.archive_identifier)
        self.assertEqual(mock_overriden_delete.call_count, 1)

    @mock.patch.object(ArchiveModel, "save")
    def test_restore_restores(self, mock_save):
        instance = ArchiveModel(name="one", pk=1, id=1)

        instance.archive()
        self.assertEqual(instance.pk, instance.archive_identifier)

        instance.restore()
        self.assertNotEqual(instance.pk, instance.archive_identifier)

    def test_archive_identifier_matches_pk_type(self):
        @archivable
        class IntModel(models.Model):
            id = models.AutoField(primary_key=True)

        @archivable
        class CharModel(models.Model):
            id = models.CharField(primary_key=True, max_length=10)

        @archivable
        class NoSpecificPK(models.Model):
            pass

        self.assertEqual(models.BigIntegerField, IntModel._meta.get_field("archive_identifier").__class__)
        self.assertEqual(models.BigIntegerField, NoSpecificPK._meta.get_field("archive_identifier").__class__)
        self.assertEqual(models.CharField, CharModel._meta.get_field("archive_identifier").__class__)
        self.assertEqual(10, CharModel._meta.get_field("archive_identifier").max_length)

        # testing scenario when we have StopIteration raised
        ArchiveModel._meta.fields = []
        _add_field_to_class(ArchiveModel, 'pk_archive')
        self.assertEquals(models.BigIntegerField, ArchiveModel._meta.get_field("pk_archive").__class__)

    def test_replace_manager_use_default(self):
        del ArchiveModel.objects
        _replace_manager(ArchiveModel, 'some_manager')
        self.assertEquals(models.Manager, getattr(ArchiveModel, "with_archived").__class__)

    def test_unique_together(self):
        @archivable
        class UniqueTogetherModel(models.Model):
            name = models.CharField(max_length=100)
            other_name = models.CharField(max_length=100)

            class Meta:
                unique_together = (('name', 'other_name'),)

        self.assertFalse(('name', 'other_name') in UniqueTogetherModel._meta.unique_together)
        self.assertTrue(('name', 'other_name', 'archive_identifier') in UniqueTogetherModel._meta.unique_together)

    def test_is_archived_property(self):
        instance = ArchiveModel(name="one", pk=1)
        self.assertFalse(instance.is_archived)
        instance.archive_identifier = 1
        self.assertTrue(instance.is_archived)
