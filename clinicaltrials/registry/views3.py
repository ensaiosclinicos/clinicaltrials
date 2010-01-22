#coding: utf-8

from django import forms
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from clinicaltrials.registry.models import ClinicalTrial, TrialNumber

TRIAL_FORMS = ['TrialIdentificationForm', 'SponsorsForm', 
               'HealthConditionsForm', 'InterventionsForm',
               'RecruitmentForm', 'StudyTypeForm','OutcomesForm',
               'DescriptorForm',]

EXTRA_SECONDARY_IDS = 2

def edit_trial_index(request, trial_pk):
    ''' start view '''
    links = []
    for i, name in enumerate(TRIAL_FORMS):
        data = dict(label='form.title', form_name=name)
        data['step'] = 'step_' + str(i + 1)
        data['icon'] = '/media/img/admin/icon_alert.gif'
        data['msg'] = 'Blank fields'
        links.append(data)
    return render_to_response('registry/trial_index.html', 
                              {'trial_pk':trial_pk,'links':links})
    
class ReviewModelForm(forms.ModelForm):
    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
        top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
        output, hidden_fields = [], []
        for name, field in self.fields.items():
            bf = BoundField(self, field, name)
            bf_errors = self.error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
            if bf.is_hidden:
                if bf_errors:
                    top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
                hidden_fields.append(unicode(bf))
            else:
                if errors_on_separate_row and bf_errors:
                    output.append(error_row % force_unicode(bf_errors))
                if bf.label:
                    label = conditional_escape(force_unicode(bf.label))
                    # Only add the suffix if the label does not end in
                    # punctuation.
                    if self.label_suffix:
                        if label[-1] not in ':?.!':
                            label += self.label_suffix
                    label = bf.label_tag(label) or ''
                else:
                    label = ''
                if field.help_text:
                    help_text = help_text_html % force_unicode(field.help_text)
                else:
                    help_text = u''
                output.append(normal_row % {'errors': force_unicode(bf_errors), 'label': force_unicode(label), 'field': unicode(bf), 'help_text': help_text})
        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))
        if hidden_fields: # Insert any hidden fields in the last row.
            str_hidden = u''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                if not last_row.endswith(row_ender):
                    # This can happen in the as_p() case (and possibly others
                    # that users write): if there are only top errors, we may
                    # not be able to conscript the last row for our purposes,
                    # so insert a new, empty row.
                    last_row = normal_row % {'errors': '', 'label': '', 'field': '', 'help_text': ''}
                    output.append(last_row)
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)
        return mark_safe(u'\n'.join(output))


class TrialIdentificationForm(forms.ModelForm):
    class Meta:
        model = ClinicalTrial
        fields = ['scientific_title','scientific_acronym',
                  'public_title','acronym']
    title = _('Trial Identification')
    # TRDS 10a
    scientific_title = forms.CharField(label=_('Scientific Title'),
                                       max_length=2000, 
                                       widget=forms.Textarea)
    # TRDS 10b
    scientific_acronym = forms.CharField(required=False,
                                         label=_('Scientific Acronym'),
                                         max_length=255)
    # TRDS 10c
    scientific_acronym_expansion = forms.CharField(required=False,
                                         label=_('Scientific Acronym Expansion'),
                                         max_length=255)
    # TRDS 9a
    public_title = forms.CharField(required=False, 
                                   label=_('Public Title'),
                                   max_length=2000, 
                                   widget=forms.Textarea)
    # TRDS 9b
    acronym = forms.CharField(required=False, label=_('Acronym'),
                              max_length=255)


def step_1(request, trial_pk):
    ct = get_object_or_404(ClinicalTrial, id=int(trial_pk))
    
    if request.POST:
        form = TrialIdentificationForm(request.POST, instance=ct)
        SecondaryIdSet = inlineformset_factory(ClinicalTrial, TrialNumber, 
                                                  extra=EXTRA_SECONDARY_IDS)
        secondary_forms = SecondaryIdSet(request.POST, instance=ct)

        if form.is_valid() and secondary_forms.is_valid():
            form.save()
            secondary_forms.save()

        if request.POST.has_key('submit_next'):
            return HttpResponseRedirect("/rg/step_2/%s/" % trial_pk)
        # FIXME: use dynamic url
        return HttpResponseRedirect("/rg/edit/%s/" % trial_pk)
    else:
        form = TrialIdentificationForm(instance=ct)
        SecondaryIdSet = inlineformset_factory(ClinicalTrial, TrialNumber, 
                                               extra=EXTRA_SECONDARY_IDS, can_delete=True)
        secondary_forms = SecondaryIdSet(instance=ct)

    forms = {'main':form, 'secondary':secondary_forms}    
    return render_to_response('registry/trial_form_step_1.html',
                              {'forms':forms,
                               'next_form_title':_('Sponsors and Sources of Support')})

