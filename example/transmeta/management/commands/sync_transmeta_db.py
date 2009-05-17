"""
 Detect new translatable fields in all models and sync database structure.

 You will need to execute this command in two cases:

   1. When you add new languages to settings.LANGUAGES.
   2. When you new translatable fields to your models.

"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction
from django.db.models import get_models

from transmeta import get_real_fieldname


def ask_for_default_language():
    print 'Available languages:'
    for i, lang_tuple in enumerate(settings.LANGUAGES):
        print '\t%d. %s' % (i+1, lang_tuple[1])
    print 'Choose a language in which to put current untranslated data.'
    while True:
        prompt = "What's the language of current data? (1-%s) " % len(lang_tuple)
        answer = raw_input(prompt).strip()
        if answer != '':
            try:
                index = int(answer) - 1
                if index < 0 or index > len(settings.LANGUAGES):
                    print "That's not a valid number"
                else:
                    return settings.LANGUAGES[index][0]
            except ValueError:
                print "Please write a number"


def ask_for_confirmation(sql_sentences, model_full_name):
    print '\nSQL to synchronize "%s" schema:' % model_full_name
    for sentence in sql_sentences:
        print '   %s' % sentence
    while True:
        prompt = '\nAre you sure that you want to execute the previous SQL: (y/n) [n]: '
        answer = raw_input(prompt).strip()
        if answer == '':
            return False
        elif answer not in ('y', 'n', 'yes', 'no'):
            print 'Please answer yes or no'
        elif answer == 'y' or answer == 'yes':
            return True
        else:
            return False


def print_missing_langs(missing_langs, field_name, model_name):
    print '\nMissing languages in "%s" field from "%s" model: %s' % \
        (field_name, model_name, ", ".join(missing_langs))


class Command(BaseCommand):
    help = "Detect new translatable fields or new available languages and sync database structure"

    def handle(self, *args, **options):
        """ command execution """
        # set manual transaction management
        transaction.commit_unless_managed()
        transaction.enter_transaction_management()
        transaction.managed(True)

        self.cursor = connection.cursor()
        self.introspection = connection.introspection

        self.default_lang = ask_for_default_language()

        all_models = get_models()
        found_missing_fields = False
        for model in all_models:
            if hasattr(model._meta, 'translatable_fields'):
                model_full_name = '%s.%s' % (model._meta.app_label, model._meta.module_name)
                translatable_fields = model._meta.translatable_fields
                db_table = model._meta.db_table
                for field_name in translatable_fields:
                    missing_langs = list(self.get_missing_languages(field_name, db_table))
                    if missing_langs:
                        found_missing_fields = True
                        print_missing_langs(missing_langs, field_name, model_full_name)
                        sql_sentences = self.get_sync_sql(field_name, missing_langs, model)
                        execute_sql = ask_for_confirmation(sql_sentences, model_full_name)
                        if execute_sql:
                            print 'Executing SQL...',
                            for sentence in sql_sentences:
                                self.cursor.execute(sentence)
                                # commit
                                transaction.commit()
                            print 'Done'
                        else:
                            print 'SQL not executed'

        transaction.leave_transaction_management()

        if not found_missing_fields:
            print '\nNo new translatable fields detected'

    def get_table_fields(self, db_table):
        """ get table fields from schema """
        db_table_desc = self.introspection.get_table_description(self.cursor, db_table)
        return [t[0] for t in db_table_desc]

    def get_missing_languages(self, field_name, db_table):
        """ get only missings fields """
        db_table_fields = self.get_table_fields(db_table)
        for lang_code, lang_name in settings.LANGUAGES:
            if get_real_fieldname(field_name, lang_code) not in db_table_fields:
                yield lang_code

    def was_translatable_before(self, field_name, db_table):
        """ check if field_name was translatable before syncing schema """
        db_table_fields = self.get_table_fields(db_table)
        if field_name in db_table_fields:
            # this implies field was never translatable before, data is in this field
            return False
        else:
            return True

    def get_sync_sql(self, field_name, missing_langs, model):
        """ returns SQL needed for sync schema for a new translatable field """
        qn = connection.ops.quote_name
        style = no_style()
        sql_output = []
        db_table = model._meta.db_table
        was_translatable_before = self.was_translatable_before(field_name, db_table)
        for lang in missing_langs:
            new_field = get_real_fieldname(field_name, lang)
            f = model._meta.get_field(new_field)
            col_type = f.db_type()
            field_sql = [style.SQL_FIELD(qn(f.column)), style.SQL_COLTYPE(col_type)]
            # column creation
            sql_output.append("ALTER TABLE %s ADD COLUMN %s" % (qn(db_table), ' '.join(field_sql)))
            if lang == self.default_lang and not was_translatable_before:
                # data copy from old field (only for default language)
                sql_output.append("UPDATE %s SET %s = %s" % (qn(db_table), \
                                  qn(f.column), qn(field_name)))
            if not f.null and lang == self.default_lang:
                # changing to NOT NULL after having data copied
                sql_output.append("ALTER TABLE %s ALTER COLUMN %s SET %s" % \
                                  (qn(db_table), qn(f.column), \
                                  style.SQL_KEYWORD('NOT NULL')))
        if not was_translatable_before:
            # we drop field only if field was no translatable before
            sql_output.append("ALTER TABLE %s DROP COLUMN %s" % (qn(db_table), qn(field_name)))
        return sql_output
