Cool Beans	
======

Cool Beans is an inventory management system hosted on Google App Engine for small businesses and vendors that is easy to setup and use. Main features include:
1. The ability to upload pictures of inventory items.
2. A unique inventory number for each item.
3. The ability to create categories for items.
4. You can easily add and track sales for each item.
5. A realtime dashboard to track sales and profits per category.

To deploy you need to create a new Google App Engine app and specify the app name in app.yaml. You need to also turn on Google Cloud services, such as Blob storage and NDB data store.



TODO:
----
1. Merge with normal POS systems in terminology (SKU not item).
2. Make categories editable!
3. Graph and D3.js integration for data.
4. Authentication!