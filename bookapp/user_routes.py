import json,requests,random,string
from functools import wraps
from flask import render_template,request,abort,redirect,flash,make_response, url_for,session

from werkzeug.security import generate_password_hash, check_password_hash
#local imports
from bookapp import app,csrf,mail,Message
from bookapp.models import db,Book,User,Category,State, Lga, Reviews,Contact, Donation
from bookapp.forms import *


def login_required(f): #from functools import wraps
    @wraps(f)#this ensures that details(meta data) about the original function f, that is being decorated is still available...
    def login_check(*args,**kwargs):
        if session.get("userloggedin") !=None:
            return f(*args,**kwargs)
        else:
            flash("Access Denied")
            return redirect('/login')
    return login_check
#To use login_required, place it after the route decorator over any route that needs authentication


@app.route("/intialize/paystack/")
@login_required
def initialize_paystack():
    deets = User.query.get(session['userloggedin'])
    #transaction details
    refno = session.get('trxno')
    trasaction_deeets = db.session.query(Donation).filter(Donation.don_refno==refno).first()
    #make a curl request to the paystack endpont
    url="https://api.paystack.co/transaction/initialize"
        
    headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_3c5244cfb8965dd000f07a4cfa97185aab2e88d5"}
        
    data={"email": deets.user_email, "amount": trasaction_deeets.don_amt,"reference":refno }
    response = requests.post(url,headers=headers,data=json.dumps(data))
    #extract json from the response coming from paystack
    rspjson = response.json()
    # return rspjson
    if rspjson['status'] == True:
        redirectURL = rspjson['data']['authorization_url']
        return redirect(redirectURL)#paystack payment page will load
    else:
        flash("Please complete the form again")
        return redirect('/donate')


@app.route("/landing")
@login_required
def landing_page():
    refno = session.get('trxno')
    transaction_deets = db.session.query(Donation).filter(Donation.don_refno==refno).first()
    url="https://api.paystack.co/transaction/verify/"+transaction_deets.don_refno
    headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_3c5244cfb8965dd000f07a4cfa97185aab2e88d5"}
    response = requests.get(url,headers=headers)
    rspjson = json.loads(response.text)
    if rspjson['status'] == True:
        paystatus = rspjson['data']['gateway_response']
        transaction_deets.don_status = 'Paid'
        db.session.commit()
        return redirect('/dashboard')
    else:
        flash("payment failed")
        return redirect('/reports/') #display all the payment reports
    
@app.route("/reports/")
@login_required
def my_reports():
    deets = User.query.get(session.get('userloggedin'))
    return render_template("user/reports.html",deets=deets)


@app.route("/explore", methods=['POST','GET'])
def explore():
    books = db.session.query(Book).filter(Book.book_status=='1').all()
    cats = db.session.query(Category).all()
    
    return render_template('user/explore.html', books=books, cats=cats)  

@app.route('/search/book')
def search_book():
    cate = request.args.get('category')
    title = request.args.get('title') 
    search_title = "%"+title+"%" # "%{}%".format(title)
    #run query
    if cate =="":
        result = db.session.query(Book).filter(Book.book_title.ilike(search_title)).all()
    else:
        result = db.session.query(Book).filter(Book.book_catid ==cate).filter(Book.book_title.ilike(search_title)).all()

    #result = [<Book 1>, <Book 2>, <Book 3>] 
    toreturn =""
    for r in result:
        toreturn = toreturn + f"<div class='col'><img src='/static/uploads/{r.book_cover}' class='img-fluid bk'><div class='deets'><h6><a href='/review/{r.book_id}'>{r.book_title}</a></h6><p><i>{r.catdeets.cat_name}</i></p><p><button class='btn btn-sm btn-warning'{len(r.bookreviews)}>Reviews</button></p></div></div>"
    
    return toreturn


    


    
    
@app.route("/sendmail/")
def send_email():
    file = open('requirements.txt')
    msg = Message(subject="Adding Heading to Email From BookWorm",sender="From BookWorm Website",recipients=["moatacad@gmail.com"])
    
    msg.html="""<h1>Welcome Home!</h1>
            <img src='https://images.pexels.com/photos/12246481/pexels-photo-12246481.jpeg' width='300'> <hr>"""
            
    msg.attach("SpecifyNameForTheAttchment.txt", "application/text", file.read())
    mail.send(msg)
    return "done"

@app.route("/ajaxopt/",methods=['GET','POST'])
def ajax_options():
    cform = ContactForm()
    if request.method=='GET':
        return render_template("user/ajax_options.html",cform=cform)
    else:
        email = request.form.get('email') 
        #insert into db
        cont = Contact.query.filter(Contact.contact_email==email).first()
        if cont: #email exists
            msg2return ={'message':'Email Exists','bsclass':"alert alert-danger"}
        else:
            contact = Contact(contact_email=email)
            db.session.add(contact)
            db.session.commit()
            msg2return ={'message':'Email added','bsclass':"alert alert-success"}
        
        return json.dumps(msg2return)
        



@app.route("/dependent/")
def dependent_dropdown():
    #write a query that will fetch all the states from state table
    states = db.session.query(State).all()
    return render_template("user/show_states.html",states=states)

@app.route("/lga/<stateid>")
def load_lgas(stateid):
    records = db.session.query(Lga).filter(Lga.state_id==stateid).all()
    str2return = "<select class='form-control' name='lga'>"
    for r in records:
        optstr = f"<option value='{r.lga_id}'>"+ r.lga_name+"</option>"
        str2return = str2return + optstr
    str2return =str2return + "</select>"    
    return str2return
    

def generate_string(howmany):#call this function as generate_string(10)
    x = random.sample(string.digits,howmany)   
    return ''.join(x)

@app.route("/donate/", methods=['POST',"GET"])
@login_required
def donation():
    donform = DonationForm()    
    if request.method =='GET':
        deets = db.session.query(User).get(session['userloggedin'])
        return render_template("user/donation_form.html", donform=donform,deets=deets)
    else:
        if donform.validate_on_submit():
            #retrieve form data
            amt = float(donform.amt.data) * 100
            donor = donform.fullname.data
            email = donform.email.data
            #generate a transaction reference for this transaction
            ref = 'BW' + str(generate_string(8))
            #insert into db (save details of trx)
            donation = Donation(don_amt=amt,don_userid=session['userloggedin'],don_email=email,don_fullname=donor,don_status='pending',don_refno=ref)
            db.session.add(donation)
            db.session.commit()
            #save the reference no in session
            session['trxno'] = ref
            #redirect to a confirmation page
            return redirect("/confirm_donation")
        else:
            deets = db.session.query(User).get(session['userloggedin'])
            return render_template("user/donation_form.html", donform=donform,deets=deets)
            
@app.route('/confirm_donation/')
@login_required
def confirm_donation():
    '''we want to display the details of the transaction saved from previous page'''
    deets = db.session.query(User).get(session['userloggedin'])
    if session.get('trxno') == None:#means they are visiting here directly
        flash("Please Complete this form", category='error')
        return redirect("/donate")
    else: #TO DO: create donation_confirmation.html
        donation_deets = Donation.query.filter(Donation.don_refno==session['trxno']).first()
        return render_template("user/donation_confirmation.html",donation_deets=donation_deets,deets=deets)
    

 
 
 
 
 
 
 

@app.route("/contact/")
def ajax_contact():
    data = "I am a string coming from the server" #may also be fetched from db
    return render_template("user/ajax_test.html",data=data)

    
@app.route("/submission/", methods=['POST',"GET"])
def ajax_submission():
    '''this route will be visited by ajax silently'''
    # user = request.args.get('fullname')
    user = request.form.get('f')
    
    if user != "" and user != None:
        return f"Thank you {user} for completing the form"
    else:
        return "Please complete the form"


@app.route('/checkusername/')
def checkusername():
    email = request.args.get('username')
    #TO DO: retrieve the email coming from frontend
    query = db.session.query(User).filter(User.user_email==email).first()
    if query:
        return "Email is taken"
    else:
        return "Email is okay, go ahead pls."


@app.route("/favourite")
def favourite_topics():
    bootcamp = {'name':'olusegun','topics':['html','css','python']}   
    cats = db.session.query(Category).all()
    # category=[]
    # for c in cats:
    #     category.append(c.cat_name)
    
    category= [c.cat_name for c in cats]
    return json.dumps(category,indent=3)
    
    
    
    
@app.route("/profile", methods=['GET','POST'])
@login_required
def edit_profile():
    id = session.get('userloggedin')
    userdeets = db.session.query(User).get(id)
    pform = ProfileForm()
    if request.method =='GET':
        return render_template('user/edit_profile.html',pform=pform,userdeets=userdeets)
    else:
        if pform.validate_on_submit():
            fullname = request.form.get('fullname') #pform.fullname.data
            userdeets.user_fullname = fullname
            db.session.commit()
            flash("profile updated")
            return redirect('/dashboard')
        else:
            return render_template("user/edit_profile.html",pform=pform,userdeets=userdeets)
        





@app.route("/changedp/", methods=['GET',"POST"])
@login_required
def changedp():
    id = session.get('userloggedin')
    userdeets = db.session.query(User).get(id)
    dpform = DpForm()
    if request.method =="GET":
        return render_template("user/changedp.html",dpform=dpform,userdeets=userdeets)
    else:#form is being submitted
        if dpform.validate_on_submit():
            pix = request.files.get('dp')
            filename = pix.filename #we can rename to avoid name clash
            pix.save(app.config['USER_PROFILE_PATH']+filename)#this has been defined in config
            userdeets.user_pix = filename
            db.session.commit()
            flash("Profile picture updated",category="info")
            return redirect(url_for('dashboard'))
        else:
            return render_template("user/changedp.html",dpform=dpform,userdeets=userdeets)



@app.route("/viewall/")
def viewall():
    books = db.session.query(Book).filter(Book.book_status=="1").all()
    return render_template("user/viewall.html",books=books)



@app.route("/logout")
def logout():
    if session.get('userloggedin')!=None:
        session.pop('userloggedin',None)
    return redirect('/')
#if you have done the above, visit the logout link to log your user out.. you will discover that the menu is no longer showing.
#To make it interesting.. link this route to the signout link on home_layout.html so that you will not need to visit logout manually
    
        
@app.route("/dashboard")
def dashboard():
    if session.get('userloggedin') !=None:
        id = session.get('userloggedin')
        userdeets = User.query.get(id)
        return render_template("user/dashboard.html",userdeets=userdeets)
    else:
        flash("You need to login to access this page",category='error')
        return redirect("/login")





@app.route('/login',methods=['POST',"GET"])
def login():
    if request.method =="GET":
        return render_template('user/loginpage.html')
    else:
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        deets = db.session.query(User).filter(User.user_email==email).first()
        if deets != None:
            hashed_pwd = deets.user_pwd
            if check_password_hash(hashed_pwd,pwd) == True:
                session['userloggedin'] =deets.user_id
                return redirect("/dashboard")
            else:
                flash("invalid crededials, try again",category='error')  
                return redirect("/login")  
        else:
            flash("invalid crededials, try again",category='error')  
            return redirect("/login")  
       

@app.route("/register/",methods=["GET","POST"])
def register():
    regform=RegForm()   
    if request.method =="GET" :
        return render_template("user/signup.html",regform=regform)
    else:
        if regform.validate_on_submit(): #retrieve form data
            fullname = regform.fullname.data
            email=regform.email.data #request.form.get('email')
            # from werkzeug.security import generate_password_hash, check_password_hash
            pwd = regform.pwd.data
            hashed_pwd = generate_password_hash(pwd)
            u = User(user_fullname=fullname,user_email=email,user_pwd=hashed_pwd)
            db.session.add(u)
            db.session.commit()
            flash("An account has been created for you. Please login.",category='info')
            return redirect('/login')
        else:
            return render_template("user/signup.html",regform=regform)
        
        
        
        
@app.route('/submit_review/',methods=['POST'])
@login_required
def submit_review():#retrieve form data and insert into db
    title = request.form.get('title')
    content = request.form.get("content")
    userid = session['userloggedin']
    book = request.form.get('book')
    br = Reviews(rev_title=title,rev_text=content, rev_userid=userid,rev_bookid=book)
    db.session.add(br)
    db.session.commit()
    
    retstr = f"""<article class="blog-post">
        <h5 class="blog-post-title">{title}</h5>
        <p class="blog-post-meta">Reviewed just now by <a href="#">{br.reviewby.user_fullname}</a></p>
        <p>{content}</p>
        <hr> 
      </article>"""    
    return retstr




@app.route("/myreviews/")
@login_required
def myreviews():
    id = session['userloggedin']
    userdeets =db.session.query(User).get(id)
    return render_template('user/myreviews.html',userdeets=userdeets)







@app.route('/books/details/<id>')
def book_details(id):
    book = Book.query.get_or_404(id)   
 
    return render_template("user/reviews.html", book=book)



@app.route("/")
def home_page():
    books =db.session.query(Book).filter(Book.book_status=="1").all()
    try:
        response = requests.get('http://127.0.0.1:5000/api/v1.0/listall') #import requests
        rsp = json.loads(response.text) #response.json()
    except:
        rsp =None  #if the server is unreacheable...  
    return render_template("user/home_page.html", books=books,rsp=rsp)




@app.after_request
def after_request(response):
    #To solve the problem of loggedout user's details being cached in the browser
    response.headers["Cache-Control"]="no-cache, no-store, must-revalidate"
    return response 

# @app.before_request
# def before_request():
#     if session.get('userloggedin') != None:
#         user = session.get('userloggedin')
#         userdeets = db.session.query(User).get(user) 
#         session['lump']=userdeets
#     return  