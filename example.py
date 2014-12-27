import webapp2
import os
import jinja2
import urllib2
import urllib
import json
import random
import collections

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.api import images
from webapp2_extras import sessions

config = {}
config['webapp2_extras.sessions'] = dict(secret_key='')
#upload_url_rpc = blobstore.create_upload_url_async('/upload')
#upload_url = upload_url_rpc.get_result()

class Counter(ndb.Model):
    counter = ndb.StringProperty(required=True)

class Category(ndb.Model):
    category = ndb.StringProperty(required=True)

class Item(ndb.Model):
    picture_url = ndb.StringProperty(required=True)
    inventory_number = ndb.StringProperty(required=True)
    status = ndb.StringProperty(required=True)
    buying_price = ndb.StringProperty(required=True)
    expected_sale_price = ndb.StringProperty(required=True)
    sale_price = ndb.StringProperty(required=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    conversion_rate  = ndb.StringProperty(required=True)
    quantity = ndb.StringProperty(required=True)
    category = ndb.StringProperty(required=False)
    sales = ndb.StringProperty(repeated=True)
    
class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
fac
        """
        return self.session_store.get_session()
    

#Left in to eventually forward to login page
class HomeHandler(BaseHandler):
    def get(self):        
            self.redirect("/portal")

        
class ServiceHandler(BaseHandler):
    def get(self):
      template = jinja_environment.get_template('form.html')
      upload_url = blobstore.create_upload_url('/upload')      
      query = Category.query(ancestor=ndb.Key('Category','chetna')).order(Category.category)
      categories = [dict([('category',q.category)] ) for q in query.iter()]        

      self.response.out.write(template.render(dict(
        url = upload_url, categories = categories 
      )))
            
    def post(self):
        
        blob_key = self.request.get('imagekey')
        blob_reader = blobstore.BlobReader(blob_key,buffer_size=1048576)
        
        
        #update the curr inventory
        counter_key = ndb.Key('Counter','chetna')
        curr_counter = counter_key.get() 
        inventory_number = None;
        
        if  curr_counter == None:
            curr_counter = Counter(id = 'chetna', counter="100000")
            inventory_number = "100000"
        else:
            inventory_number = str(int(curr_counter.counter)+1) 
            curr_counter.counter = inventory_number
            
        curr_counter.put()
        
        item = Item(parent = ndb.Key('Item','chetna'),
                    inventory_number = inventory_number,
                    picture_url=images.get_serving_url(blob_key),
                    buying_price = self.request.get("buying_price"),
                    expected_sale_price = self.request.get("expected_sale_price"),
                    sale_price  = "0",
                    conversion_rate = self.request.get("conversion_rate"),
                    status = "unsold",
                    category = self.request.get("category"),
                    quantity = self.request.get("quantity")
                  )
    
    
        item.put()
        self.response.out.write(inventory_number)
#        self.redirect('/redirect?submit_post&inventory_number='+inventory_number)

     
class ModalHandler(BaseHandler):

            
    def post(self):
        inventory_number = self.request.get("inventory_number");
        category = self.request.get("category")
        buying_price = self.request.get("buying_price")
        quantity = self.request.get("quantity")
        expected_sale_price = self.request.get("expected_sale_price")
        print inventory_number,category,buying_price,quantity,expected_sale_price

        query = Category.query(ancestor=ndb.Key('Category','chetna')).order(Category.category)
        categories = [dict([('category',q.category)] ) for q in query.iter()]        
        

        queries = Item.query(Item.inventory_number==inventory_number, ancestor=ndb.Key('Item','chetna')) #better be unique !!!!
        query  = queries.fetch()[0]
        query.category = category
        query.buying_price = buying_price
        query.quantity = quantity
        query.expected_sale_price = expected_sale_price
        query.put()
        template_row = jinja_environment.get_template('manage_row.html')

        items = build_items(queries)
        self.response.out.write(template_row.render(dict(items=items, categories = categories)))
        
        #self.redirect('/redirect?submit_post&inventory_number='+inventory_number)
     
class SettingsHandler(BaseHandler):
    def get(self):
        template = jinja_environment.get_template('settings.html')
        query = Category.query(ancestor=ndb.Key('Category','chetna')).order(Category.category)
        categories = [dict([('category',q.category)] ) for q in query.iter()]        
        print "categories", categories
        self.response.out.write(template.render(dict(categories = categories)))
        
 
    def post(self):
        category = self.request.get("new_category")
        queries = Category.query(Category.category==category, ancestor=ndb.Key('Category','chetna')).fetch() #better be unique !!!!
        if len(queries) != 0:
            self.response.out.write("duplicate")
            return
        cat = Category(parent = ndb.Key('Category','chetna'),
                            category = category)
        cat.put()
        self.response.out.write(category)

 
class SaleHandler(BaseHandler):
    def get(self):
        inventory_number = self.request.get("inventory_number")
        template = jinja_environment.get_template('sale.html')
        self.response.out.write(template.render(dict(inventory_number= inventory_number)))
            
    def post(self):
        inventory_number = self.request.get("inventory_number")
        queries = Item.query(Item.inventory_number==inventory_number, ancestor=ndb.Key('Item','chetna')).fetch() #better be unique !!!!
        if len(queries) == 0:
            self.response.out.write("Inventory Number not found!")
            return
        query = queries[0]
        status = query.status
        if status == "sold":
            self.response.out.write("This item has already been sold")
        else:
            sale_price = self.request.get("sale_price")
            query.sales.append(sale_price);
            if len(query.sales) == int(query.quantity):
                query.status = "sold"
            query.sale_price = str(self.average(query.sales))
            query.put()
            self.response.out.write("success")
            #self.redirect('/redirect?submit_post')

    def average(self, sales):
        sum = 0
        for s in sales:
            sum+=float(s)
        return (1.*sum)/len(sales)
        

class DataHandler(BaseHandler):
    def get(self):
        template = jinja_environment.get_template('data.html')
        template_rows = jinja_environment.get_template('data_row.html')
        query = Item.query(ancestor=ndb.Key('Item','chetna')).order(-Item.inventory_number)
        #USe fetch instead
        items = [q for q in query.iter()]

        cost = sum([0 if (q.conversion_rate==None) else round(float(q.buying_price)*float(q.quantity)/float(q.conversion_rate),2) for q in query.iter()])
        revenue = sum([0 if q.sale_price==None else float(q.sale_price)*float(len(q.sales)) for q in query.iter()])
        profit = revenue-cost
        
        query2 = Category.query(ancestor=ndb.Key('Category','chetna')).order(Category.category)
        categories = [q.category for q in query2.iter()]        


        rows = []
        for category in categories:
            local_items = filter(lambda x: x.category == category,items)
            d = dict()
            d['category'] = category
            d['number_of_items'] = sum([int(q.quantity) for q in local_items])
            d['number_of_items_unsold'] = sum([int(q.quantity)-len(q.sales)  for q in local_items])
            d['number_of_items_sold'] = sum([len(q.sales) for q in local_items])
            d['cost'] = sum([ 0 if (q.conversion_rate==None) else round(float(q.buying_price)*float(q.quantity)/float(q.conversion_rate),2) for q in local_items])
            d['revenue'] = sum([  0 if q.sale_price==None else float(q.sale_price)*float(len(q.sales)) for q in local_items])
            rows.append(d)

            #Do this ten times better using filter
            #rows = [dict([                      
            #('category',category),
            #('number_of_items',sum([int(q.quantity) for q in items if q.category==category])),
            #('number_of_items_unsold',sum([int(q.quantity)-len(q.sales)  for q in items if (q.category==category)])),
            #('number_of_items_sold',sum([len(q.sales) for q in items if (q.category==category) ])),
            #('average_cost',sum([ 0 if (q.conversion_rate==None) else round(float(q.buying_price)/float(q.conversion_rate),2) for q in items if q.category==category ])/len([0 for q in items if q.category==category])),
        #('cost',sum([ 0 if (q.conversion_rate==None) else round(float(q.buying_price)*float(q.quantity)/float(q.conversion_rate),2) for q in items if q.category==category ])),
           # ('revenue',sum([  0 if q.sale_price==None else float(q.sale_price)*float(len(q.sales)) for q in items if q.category==category ] ) for category in categories]


        self.response.out.write(template.render(dict(cost=str(round(cost, 2)), revenue=str(round(revenue, 2)),profit=str(round(profit, 2)),rows=template_rows.render(rows=rows))))



class ManageHandler(BaseHandler):
    def get(self):
        template = jinja_environment.get_template('manage.html')
        template_row = jinja_environment.get_template('manage_row.html')
        query = Item.query(ancestor=ndb.Key('Item','chetna')).order(-Item.inventory_number)
        items = build_items(query,0)
        
        #Use this to do some bulk changes!!!
        # for q in query:
        #     if q.status == "sold" and len(q.sales)==0:
        #         q.sales.append(q.sale_price)
        #         print q.inventory_number
        #         q.put()
            #q.category = "Cushion Covers"
        query = Category.query(ancestor=ndb.Key('Category','chetna')).order(Category.category)
        categories = [dict([('category',q.category)] ) for q in query.iter()]        
        
        self.response.out.write(template.render(dict(rows = template_row.render(dict(items = items,categories=categories)),categories=categories)))
    
    def post(self):
        if self.request.path == '/manage/deletepost':
            inventory_number = self.request.get("postkey")
            query = Item.query(Item.inventory_number==inventory_number, ancestor=ndb.Key('Item','chetna')).fetch()[0] #better be unique !!!!
            query.key.delete()
            self.response.out.write("success");
        
        elif self.request.path == '/manage/query_category':
            template_row = jinja_environment.get_template('manage_row.html')
            category = self.request.get("category")
            print category
            queries = Item.query(Item.category==category, ancestor=ndb.Key('Item','chetna')).order(-Item.inventory_number) #better be unique !!!!
            items = build_items(queries)
            self.response.out.write(template_row.render(dict(items=items)))

        elif self.request.path == '/manage/query_inventory_number':
            print self.request
            template_row = jinja_environment.get_template('manage_row.html')
            inventory_number = self.request.get("inventory_number")
            print "inventory_number", inventory_number
            queries = Item.query(Item.inventory_number==inventory_number, ancestor=ndb.Key('Item','chetna')) #better be unique !!!!
            if queries.count() == 0:
                self.response.out.write("fail")
            else:

                items = build_items(queries)
                self.response.out.write(template_row.render(dict(items=items)))
            

def build_items(query,limit=0):
    items = []
    if limit == 0:
        items = [dict([('inventory_number', q.inventory_number),
                           ('key',str(q.key.pairs()[0][1]) +"_"+ str(q.key.pairs()[1][1])),
                           ('date', q.date.date()), 
                           ('status', q.status),
                           ('picture_url', q.picture_url),
                           ('expected_sale_price',("0" if q.expected_sale_price== None else q.expected_sale_price)),
                           ('buying_price',("0" if (q.conversion_rate==None) else str(round(float(q.buying_price)/float(q.conversion_rate),2)))),
                           ('rupees_buying_price',q.buying_price),
                           ('sale_price',("0" if q.sale_price==None else q.sale_price)),
                           ('category',q.category),
                           ('quantity',q.quantity),
                           ('quantity_sold',str(len(q.sales)))
                       ] ) for q in query.fetch()]
    else:
        items = [dict([('inventory_number', q.inventory_number),
                           ('key',str(q.key.pairs()[0][1]) +"_"+ str(q.key.pairs()[1][1])),
                           ('date', q.date.date()), 
                           ('status', q.status),
                           ('picture_url', q.picture_url),
                           ('expected_sale_price',("0" if q.expected_sale_price== None else q.expected_sale_price)),
                           ('buying_price',("0" if (q.conversion_rate==None) else str(round(float(q.buying_price)/float(q.conversion_rate),2)))),
                           ('rupees_buying_price',q.buying_price),
                           ('sale_price',("0" if q.sale_price==None else q.sale_price)),
                           ('category',q.category),
                           ('quantity',q.quantity),
                           ('quantity_sold',str(len(q.sales)))
                       ] ) for q in query.fetch(limit)]
            
    return items

        
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):        
    def post(self):
        upload_files = self.get_uploads('files[]')
        blob_info = upload_files[0]
        obj = {
            'upload_image_key': str(blob_info.key()) 
            } 
        self.redirect("/redirect?"+urllib.urlencode(obj))
        

class RedirectHandler(BaseHandler):    
    def get(self):
        if self.request.get('upload_image_key') != '': 
            obj = {
                'key': self.request.get('upload_image_key')
                } 
            print "make a key"+obj['key']
            self.response.headers['Content-Type'] = 'application/json'   
            self.response.out.write(json.dumps(obj))
        # else:# self.request.get('submit_post') != '':
        #     print "request "+self.request.get("inventory_number")
        #     #self.redirect('/end?inventory_number='+self.request.get("inventory_number"))
        #     template = jinja_environment.get_template('end.html')
        #     print "end "+self.request.get("inventory_number")
        #     dd = {"inventory_number":self.request.get("inventory_number")}
        #     self.response.out.write(template.render(dd))

class PortalHandler(BaseHandler):
    def get(self):
      template = jinja_environment.get_template('portal.html')
      self.response.out.write(template.render())
 

class EndHandler(BaseHandler):
    def get(self):
      template = jinja_environment.get_template('end.html')
      print "end "+self.request.get("inventory_number")
      dd = {"inventory_number":self.request.get("inventory_number")}
      self.response.out.write(template.render(dd))


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname("templates/base.html")) , autoescape=True, extensions=['jinja2.ext.autoescape'])

application = webapp2.WSGIApplication(
    [('/settings',SettingsHandler),('/settings/post',SettingsHandler),('/manage', ManageHandler),('/manage/[^/]+', ManageHandler),('/', HomeHandler), ('/portal', PortalHandler),('/upload',UploadHandler), ('/service', ServiceHandler),('/service/post',ServiceHandler),('/modal/post',ModalHandler),('/sale', SaleHandler),('/sale/post',SaleHandler),('/redirect?',RedirectHandler),('/data',DataHandler),('/end?',EndHandler)],
    debug=True,
    config=config
)

        # for group in select_groups:
        #     self.graph.put_wall_post(description, {"link":"http://facebook.com/%s"%(posted_id),"picture":images.get_serving_url(blob_key)}, group)

#('/login', LoginHandler),  , ('/manage', ManageHandler), ('/manage/deletepost', ManageHandler), , , ('/logout', LogoutHandler), 





#('/serve/([^/]+)?',ServeHandler),('/upload',UploadHandler),('/app/picture_upload',PictureHandler),('/app/data_upload',DataHandler)
# class PictureHandler(blobstore_handlers.BlobstoreUploadHandler):
#     def get(self):
#         upload_url = blobstore.create_upload_url("/upload")
#         print "upload_url",upload_url
#         self.response.out.write(upload_url);

# class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
#     def post(self):
#         print self.get_uploads()
#         upload_files = self.get_uploads()[0]
#         #blob_info = upload_files
#         #self.redirect('/serve/%s' % blob_info.key())

# class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
#   def get(self, resource):
#       resource = str(urllib.unquote(resource))
#       blob_info = blobstore.BlobInfo.get(resource)
#       self.send_blob(blob_info)

# class DataHandler(BaseHandler):
#     def post(self):
#         print self.request.get("message");
#         self.response.out.write("Got Data")
