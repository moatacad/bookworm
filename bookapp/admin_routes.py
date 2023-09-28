import random,string,os
from flask import render_template,request,abort,redirect,flash,make_response, url_for,session

#local imports
from bookapp import app,csrf
from bookapp.models import db, Admin, Book,Category
from bookapp.forms import *

def generate_string(howmany):#call this function as generate_string(10)
    x = random.sample(string.ascii_lowercase,howmany)   
    return ''.join(x)

@app.route("/admin/edit/book/<id>/",methods=['GET',"POST"])
def edit_book(id):
    if session.get("adminuser")== None or session.get("role") != 'admin':
        return redirect(url_for('admin_login'))
    else:
        if request.method =='GET':
            deets= db.session.query(Book).filter(Book.book_id==id).first_or_404()
            cats=db.session.query(Category).all()
            return render_template("admin/editbook.html",deets=deets,cats=cats)
        else:#retrieve form data here...
            #in order to update the book details, 
            book_2update = Book.query.get(id)
            current_filename = book_2update.book_cover 
            
            book_2update.book_title = request.form.get('title')
            book_2update.book_catid = request.form.get('category')
            book_2update.book_status = request.form.get('status')
            book_2update.book_desc = request.form.get('description')
            book_2update.book_publication = request.form.get('yearpub')
            
            cover = request.files.get('cover')
            #check if file was selected for upload
            if cover.filename !="":
                name,ext = os.path.splitext(cover.filename)
                if ext.lower() in ['.jpg','.png','.jpeg']:
                    #upload the file, its allowed
                    newfilename = generate_string(10) + ext
                    cover.save("bookapp/static/uploads/"+newfilename)
                    book_2update.book_cover = newfilename
                else:
                    flash("The extension of the book cover wasnt included")
            db.session.commit()
            flash('Book details was updated')           
            return redirect('/admin/books/')





#re.sub("pattern", "replacement", Stringr, count_replacementno)
#to replace space with _: re.sub(" ","_",filename)
@app.route('/admin/delete/<id>/')
def book_delete(id):
    book = db.session.query(Book).get_or_404(id)
    #lets get the name of the file attached to this book
    filename = book.book_cover
    #first delete the file before deleting the book from db 
    if filename != None and filename !='default.png' and os.path.isfile("bookapp/static/uploads/"+filename):
        os.remove("bookapp/static/uploads/"+filename) #import os at the top
    db.session.delete(book)
    db.session.commit()
    flash("Book has been deleted!")
    return redirect(url_for("all_books"))

    
    
    
    


@app.route("/admin/addbook", methods=["GET","POST"])
def addbook():
    if session.get("adminuser")== None or session.get("role") != 'admin':
        return redirect(url_for('admin_login'))
    else:
        if request.method =="GET":
            cats = db.session.query(Category).all()
            return render_template('admin/addbook.html',cats=cats)
        else:
            #retrieve file
            allowed = ['png','jpg']
            fileobj = request.files['cover']
            filename = fileobj.filename 
            
            newname = "default.png" #default cover
                                    
            if filename =='': #no file was uploaded
                flash("Book Cover not included",category='error')
            else: #file was selected
                pieces = filename.split('.')
                ext = pieces[-1].lower()
                if ext in allowed:
                    newname = str(int(random.random()*10000000000))+filename #to make sure it is random
                    fileobj.save("bookapp/static/uploads/"+newname)
                else:
                    flash("File extension not allowed, file was not uploaded",category='error') 
                       
            #retrieve all the form data
            title = request.form.get('title')
            category = request.form.get('category')
            status = request.form.get('status')
            description = request.form.get('description')
            yearpub = request.form.get('yearpub')
            bookcover = newname
            #insert into db
            bk = Book(book_title=title,book_desc=description,book_publication=yearpub,book_catid=category,book_status=status,book_cover=newname)
            db.session.add(bk)
            db.session.commit()
            if bk.book_id:
                flash("book has been added")
            else:
                flash("Please try again")            
            return redirect(url_for('all_books'))
       
        
@app.route("/admin/books/")
def all_books():
    if session.get("adminuser")== None or session.get("role") != 'admin':
        return redirect(url_for('admin_login'))
    else:
        books =db.session.query(Book).all()#Book.query.all()    
        return render_template("admin/allbooks.html",books=books)
    




@app.route("/admin/logout")
def admin_logout():
    if session.get("adminuser") !=None:#he is still logged in
        session.pop("adminuser",None)
        session.pop("role",None)
        flash("You have logged out",category='info')
        return redirect(url_for('admin_login'))
    else:#she is logged out already
        return redirect(url_for('admin_login')) 
        #if you have done the above, link this route to admin_layout.html

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get("adminuser")== None or session.get("role") != 'admin':#means he is not logged in..
        return redirect(url_for('admin_login'))
    else:
        return render_template("admin/dashboard.html")        
        
        



@app.route("/admin/login/", methods=["GET","POST"])
def admin_login():
    if request.method=='GET':
        return render_template('admin/login.html')
    else:
        #retrieve form data
        username = request.form.get("username")
        pwd = request.form.get('pwd')
        #check if it is in database, 
        check = db.session.query(Admin).filter(Admin.admin_username==username,Admin.admin_pwd==pwd).first()
        #if it is in db, save in session and redirect to dashboard
        if check:#it is in db, save session
            session['adminuser']=check.admin_id
            session['role']='admin'
            return redirect(url_for('admin_dashboard'))
        else: #if not, save message in flash, redirect to login again
            flash('Invalid Login',category='error')
            return redirect(url_for('admin_login'))
        #TO DO: within login.html, retrieve and display the flash message. Test the above to see if it works
        
@app.route("/admin/")
def admin_page():
    if session.get("adminuser")== None or session.get("role") != 'admin':#means he is not logged in..
        return render_template("admin/login.html")
    else:
        return redirect(url_for('admin_dashboard'))
 






@app.after_request
def after_request(response):
    #To solve the problem of loggedout user's details being cached in the browser
    response.headers["Cache-Control"]="no-cache, no-store, must-revalidate"
    return response 

