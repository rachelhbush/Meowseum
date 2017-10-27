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

