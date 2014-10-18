#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
import urllib2

class MainHandler(webapp2.RequestHandler):
    def get(self):
        #self.response.write('Hello world!')

        template = jinja_environment.get_template('form.html')
        self.response.out.write(template.render(
        	current_user='a'
        ))

class FormHandler(webapp2.RequestHandler):

	def post(self):

	    description = self.request.get('description_input')
	    print description
	    
	    # feedbackEntity = Feedback(parent=feedback_key(email+feedback[0:min(10,len(feedback))]))
	    # feedbackEntity.email = self.request.get('email_input')
	    # feedbackEntity.phone_model = self.request.get('phone_model_input')
	    # feedbackEntity.feedback = self.request.get('feedback_input')
	    
	    # feedbackEntity.put()

class FileHandler(webapp2.RequestHandler):
	def post(self):
		print 'hello'
		#print self.request
	    #description = self.request.get('description_input')
	    #print description
	
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)

app = webapp2.WSGIApplication([
    ('/form',MainHandler),('/form/post',FormHandler),('/form/file',FileHandler)
], debug=True)
