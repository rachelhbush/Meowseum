from django import forms

# Custom widgets
class HTML5DateInput(forms.DateInput):
    input_type='date'

# Custom form fields
class HTML5DateField(forms.DateField):
    # This assumes a North America localization.
    input_formats = ['%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%m/%d/%y']
    widget = HTML5DateInput(format='%m/%d/%Y', attrs={'placeholder':'mm/dd/yyyy'} )

class MultipleChoiceField(forms.MultipleChoiceField):
    # Change the default widget from <select multiple> to a checkbox group. <select multiple> has become discouraged because most sites which incorporate it have to explain the interface.
    # All the common alternatives scripted with JavaScript incorporate checkboxes, including those which look similar to <select multiple>. 
    widget = forms.CheckboxSelectMultiple()

# Custom Forms and ModelForms

# Summary: This ModelForm subclass supports specifying a RadioSelect (radio button) widget by only specifying the widgets= section of class Meta.
# Description: In the default ModelForm, if the field is optional, it adds a "----" option to the beginning of a series of radio buttons unless the
# field is a BooleanField. This is usually undesired because the user can choose this value by leaving the field blank, but it is there because the
# widget's ChoiceField is shared with the <select> dropdown. The only drawback is a rare atypical behavior that if the ModelForm has an overriding
# field and a widget for this field in class Meta simultaneously, then the overriding field's choices will be ignored.
class RadioModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm,self).__init__(*args, **kwargs)
        if self._meta.widgets != None:
            for field, widget in self._meta.widgets.items():
                try:
                    if widget == forms.RadioSelect:
                        # Obtain the choices from the model, without the choice for a blank field unless it is explicitly provided. As far as I know,
                        # there is no easy way to detect which fields are overriding. When the ModelForm field isn't an overriding one, self.fields[field].choices
                        # is identical to the model's choices' argument except for the ('', '------') option, and testing for that would be too complicated to take
                        # the time to program because Django's choices structure can vary considerably in order to accomodate different structures with <optgroup>. 
                        self.fields[field].choices = self._meta.model._meta.get_field(field).choices
                except AttributeError:
                    # The field has no choices attribute because the programmer used a choice-related widget without defining choices. Django will render a blank space in the form.
                    pass
