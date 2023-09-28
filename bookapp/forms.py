from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired,FileAllowed
from wtforms import StringField, SubmitField,TextAreaField,PasswordField
from wtforms.validators import Email, DataRequired,EqualTo,Length


class DonationForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired()])
    email = StringField("Email",validators=[Email(message="Invalid Format"),DataRequired()])
    amt = StringField("Specify Amount",validators=[DataRequired()])    
    btnsubmit = SubmitField("Continue")
    
  
  
  
  
  
  
    
    
class RegForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="The Firstname is a must!")])
    email = StringField("Email",validators=[Email(message="Invalid Email Format"),DataRequired(message="Email must be supplied")])
    pwd = PasswordField("Enter Password",validators=[DataRequired()])
    confpwd = PasswordField("Confirm Password",validators=[EqualTo('pwd',message='bros, let the two password match...')])
    btnsubmit = SubmitField("Register!")
    
class DpForm(FlaskForm):
    dp =  FileField("Upload a Profile Picture",validators=[FileRequired(),FileAllowed(['jpg', 'png','jpeg'])])
    btnupload = SubmitField("Upload Picture")
    
class ProfileForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="The Fullname is a must!")])
    btnsubmit = SubmitField("Update Profile!")
    
class ContactForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired()])
    btnsubmit = SubmitField("Subscribe...")