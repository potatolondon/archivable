# A class-decorator for archivable django-models.

The decorator adds a field called `archive_identifier` to each archivable model, which is included in any uniqueness
constraints of the models. This ensures archived objects don't interfere with non-archived ones, and archiving objects
will never trigger uniqueness errors.

Unarchiving an object can still violate uniqueness constraints - it is up the application to decide what to do in these
situations, for example merging the two objects or raising an informative error.

You should use `ArchivableModelForm` instead of `ModelForm` for any archivable models, because `ModelForm` skips validating
uniqueness on archivable models. This is because it doesn't check unique constraints involving non-editable fields, and as
`archive_identifier` is non-editable and forcefully included in every unique constraint. `ArchivableModelForm` is
simply a `ModelForm` that doesn't exclude `archive_identifier` as a non-editable field.

## Requirements
The mixin itself has no requirements, but the tests require mock.

The test app requires django, mock and coverage. Simply run `./init.sh` in the testapp directory to set everything up,
which will install dependencies into a local virtualenv.

Run `./run_tests.sh` in testapp/ to run the tests, or do `source env/bin/activate` and `./manage.py test`

## Usage

 - Add `archivable` to `INSTALLED_APPS`.
 - Decorate any classes that should be archivable with `@archivable.archivable`.
 - Archive/restore objects with `instance.archive()`/`instance.restore()`.
 - Calling `instance.delete()` will also archive objects, unless called with `force=True`, which will force actual deletion of the object.
 - `Model.objects` excludes archived objects. Use `Model.with_archived` to include them.
 - Archiving an object will trigger a `post_archive` signal, with `instance` being the only argument.
 - instance.is_archived is True for archived objects, False otherwise.
 - Replace any `ModelForm` for archivable models with `ArchivableModelForm`.
