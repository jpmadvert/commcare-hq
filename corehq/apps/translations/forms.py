from __future__ import absolute_import
from __future__ import unicode_literals
import openpyxl

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms import layout as crispy
from crispy_forms.bootstrap import StrictButton
from django.utils.translation import ugettext as _, ugettext_lazy


class ConvertTranslationsForm(forms.Form):
    upload_file = forms.FileField(label="")

    def __init__(self, domain, *args, **kwargs):
        super(ConvertTranslationsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = crispy.Layout(
            crispy.Field(
                'upload_file',
                data_bind="value: file",
            ),
            StrictButton(
                ugettext_lazy('Convert'),
                css_class='btn-primary',
                data_bind='disable: !file()',
                onclick='this.disabled=true;this.form.submit();',
                type='submit',
            ),
        )

    def clean_upload_file(self):
        uploaded_file = self.cleaned_data.get('upload_file')
        if uploaded_file:
            if uploaded_file.name.endswith('.xls') or uploaded_file.name.endswith('.xlsx'):
                workbook = openpyxl.load_workbook(uploaded_file)
                worksheet = workbook.worksheets[0]
                rows = [row for row in worksheet.iter_rows()]
                headers = [cell.value for cell in rows[0]]
                if 'source' not in headers or 'translation' not in headers:
                    raise forms.ValidationError(_("Please ensure columns 'source' and 'translation' in the sheet"))
                return uploaded_file
            elif uploaded_file.name.endswith('.po'):
                return uploaded_file
            raise forms.ValidationError(_('Unexpected file passed. Please upload xls/xlsx/po file.'))