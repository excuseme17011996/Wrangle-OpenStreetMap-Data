
# coding: utf-8

# # Wrangle OpenStreetMap Data (using MongoDB)
# ## Data Wrangling Project
# #### Data Analyst Nanodegree (Udacity)
# ##### Project No.-04
# 
# 
# 
# by Rahul Patra.
# 
# June 7, 2017.
# 
# ----------

# ## Overview :

# This project seeks to apply data munging techniques to first analyse and clean Open Street Map data for a single city and then perform an exploratory analysis of the data after importing it into a MongoDB collection.
# 
# I have choosen the Open Street Map data for Oxford England as for the last two month I had visited the Oxford. Having visited the city on quite a few occasions, I am confident that there is a lot of interesting information to be discovered through this analysis. And I'm unable to get the data over 50 MB size of the place where I actually live. This is another reason for choosing the unique popular place like Oxford.

# The data for this project was acquired from Map Zen. The compressed Oxford, England OSM XML data set can be downloaded by following this metro extract [link](https://s3.amazonaws.com/metro-extracts.mapzen.com/oxford_england.osm.bz2). The OSM file is 5.0 MB compressed and 66.2 MB uncompressed.

# In[1]:

# The following is needed at the beginning of the notebook to make sure the cells execute ok.
import sys
sys.path.append('./case_study_files')

data_name = "oxford_england"
OSMFILE = "{}.osm".format(data_name)


# ## Problems encountered in the map :

# As you would expect from any crowd-sourced data, there is evidence of inconsistent naming conventions as well as evidence of human error when the data was entered. The two main areas of inconsistency that affect this project is in the names used to describe the type of record in the data and the strings used as values within the data. It isn't feasible to analyse all values in the data, but street names are one type of value where inconsistency in values has a significant impact on the quality of the data. 
# 
# The following analysis attempts to find problems with tag key names along with suggested fixes for the problems. There is a similar analysis and set of recommendations for fixing the values used for street names.

# ### Problems related to Tag Key Names :

# In[2]:

# Find problems with tag names
import tags as tags_processor
tag_problems = tags_processor.process_map(OSMFILE)

# Additional key categories have been added in an attempt to catch additional key name patterns and minimise 
# the number of keys that fall within the 'other' category.

# The problems are defined as follows:
#   "lower", for tags that contain only lowercase letters and are valid,
#   "upper", for tags that contain upercase letters,
#   "lower_colon", for otherwise valid tags with a colon in their names,
#   "uper_colon", for tags contain both uppercase strings delimited by a colon,
#   "multiple_colons", for tags contain more than two colon seperated strings,
#   "numbers", for tags that contain a digit, and
#   "problemchars", for tags with problematic characters, and
#   "other", for other tags that do not fall into the other three categories.
print "The number of keys in each of the 'problem' categories:"
print tag_problems['counts']
unique_key_names = tags_processor.unique_tag_keys(OSMFILE)
print "There are {} unique tag key names in the data set.".format(len(unique_key_names))


# It is the tags that fall under 'problemchars' that will be particularly problematic as these tag key names aren't valid key names in MongoDB. Let's see what these tags look like and how they could be fixed.

# In[3]:

tag_problems['keys']['problemchars']


# These issues can be easily fixed by making the following replacements:
# 
# - Replace ' ' with '\_'
# - Replace '&' with '\_and\_'
# - Replace '.' with '\_'
# 
# The logic to do this has been added to the case_study_files/data.py so that the key values are tidied when the elements are being shaped.
# 
# We will also add logic to handle the keys that fall under 'upper' and 'upper_colon'. This can be fixed by ensuring that shape_element uses the lowercase version of the strings.
# 
# The key names that fall under 'multiple_colons' can be handled by adding additional nesting within the JSON data created by shape_element.
# 
# Tag key names that fall within the 'numbers' category are useful to know about, but numbers are valid characters in MongoDB strings so no additional processing is required.
# 
# It is also worth looking at the one remaining key that fall under 'other' to see why it doesn't fall within one of the other categories.

# In[4]:

set(tag_problems['keys']['other'])


# Like the tag key names that contain numbers, the hyphen is also a valid character in a MongoDB key as this one one 'other' key name is fine as it is.

# ### Problems related to street name :

# In[5]:

# Find problems with street names
import audit as street_name_auditor
street_name_auditor.audit(OSMFILE)


# The large majority of these street names are valid, but there are a few problems. There are a few cases of abbreviated street names such as 'Ave', 'Rd' and 'St'. There are also several cases of punctuations mistakes such as 'Way?' and 'Way,'. There are cases of both 'road' and 'way' being lowercase. There is also a typo where 'Reliuance Way' should be 'Reliance Way'. The oddest problems are the cases of 'Avenue 1' through 'Avenue 4'. In Kennington just outside of Oxford the main street is called 'The Avenue'. I believe these street names may be mistakes or parsing issues. They don't match any obvious street names and as a result will be treated as anomalies and ignored.
# 
# Logic has been added to case_study_files/data.py to clean up these inconsistencies.

# ### Problems related with Food :

# In[6]:

import cuisine as cuisine_auditor
food_nodes = cuisine_auditor.audit(OSMFILE)

food_nodes_with_cuisine_and_amenity = [n for n in food_nodes if 'cuisine' in n and 'amenity' in n]
food_nodes_without_cuisine = [n for n in food_nodes if 'cuisine' not in n]
food_nodes_without_amenity = [n for n in food_nodes if 'amenity' not in n]
print "Number of food nodes: {}".format(len(food_nodes))
print "Number of food nodes with a cuisine and amenity: {}".format(len(food_nodes_with_cuisine_and_amenity))
print "Number of food nodes without a cuisine: {}".format(len(food_nodes_without_cuisine))
print "Number of food nodes without an amenity: {}".format(len(food_nodes_without_amenity))


# In[7]:

from collections import Counter

amenities = []
for node in food_nodes_without_cuisine:
    amenities.append(node['amenity'])

print "Amenity counts for food nodes without a cuisine:"
print Counter(amenities)


# In[8]:

def reasonable_anomoly(n):
    return 'name' in n and ('shop' in n or 'disused' in n)
[{'name': n['name'], 'cuisine': n['cuisine']} for n in food_nodes_without_amenity if reasonable_anomoly(n)]


# In[9]:

for amenity in cuisine_auditor.food_amenities:
    cuisines = []
    relevant_nodes = [n for n in food_nodes_with_cuisine_and_amenity if n['amenity'] == amenity]
    for node in relevant_nodes:
        cuisines.append(node['cuisine'])
    print "Cuisine counts for {} nodes:".format(amenity)
    print Counter(cuisines)
    print '\n'


# In[10]:

from difflib import SequenceMatcher

def similarity_by_name(a, b):
    if 'name' in a and 'name' in b:
        a = a['name'].replace('the', '').lower()
        b = b['name'].replace('the', '').lower()
        return SequenceMatcher(None, a, b).ratio()
    else:
        return 0

subject = food_nodes_without_cuisine[0]

processed_nodes = []
food_nodes_with_same_amenity = [n for n in food_nodes_with_cuisine_and_amenity if n['amenity'] == subject['amenity']]
for node in food_nodes_with_same_amenity:
    if 'name' in node:
        processed_nodes.append({'similarity': similarity_by_name(subject, node), 'node': node})

print "Subject name: {}   Subject amenity: {} \n".format(subject['name'], subject['amenity'])
sorted_results = sorted(processed_nodes, key=lambda k: k['similarity'], reverse=True)
for result in sorted_results[:5]:
    node = result['node']
    score = '%.3f' % result['similarity']
    print "Similarity score: {}   Name: {}   Cuisine: {}".format(score, node['name'], node['cuisine'])


# This analysis shows that there are definite problems with the cuisine classifications of food nodes within the data. Of the 523 nodes analysed, 303 have amenity types but no cuisine type and 7 have a cuisine type but no amenity type. The 7 nodes that have a cuisine but are missing an amenity can be explained as follows and don't need further analysis: four are shops and don't require an amenity and two are marked as disused one of which is missing. Only 'The Oriental Condor' looks like it should have an amenity type but does not.
# 
# The 303 nodes that have food related amenities but lack a cuisine are broken down by amenity as follows:
# 
# - pub: 152 
# - cafe: 73
# - restaurant: 31 
# - fast_food: 26
# - bar: 21
# 
# I believe that the disproportionate representation of pubs within this data can be explained by either the pubs not serving food and as a result not needing a cuisine type although I find it hard to believe that Oxford has 153 pubs none of which serve food. What may be more likely is that the creators of this data assumed that a node marked as a 'pub' serves 'pub food' and as a result does not need a 'cuisine'.
# 
# An analysis of the cuisines for each of the remaining 213 nodes broken down by amenity does not show a consistent pattern. A winner take all strategy (majority cuisine by amenity) to fix the 303 problem nodes would mean assigning 'indian' to all 'restaurants' and 'chinese' to all 'fast_food' nodes. This hardly seems appropriate.
# 
# A more sophisticated strategy would be to do a similarity analysis between node names and see if appropriate cuisines could be inferred from the node names. An initial attempt at fixing the 303 problem nodes this way also proved inappropriate. A sample application of the approach resulted in 'The Tree' pub being considered most similar to 'The Gardeners Arms' pub. This is a clever result in terms of string similarity, but 'The Gardeners Arms' servers vegetarian food and a little bit of research shows that the pub at The Tree Hotel serves standard pub fair (curry, steak etc.). This illustrates why trying to infer the cuisine simply by doing a string similarity analysis on the node names will likely result in badly assigned cuisine types. For this reason, I decided not to attempt to fix the cuisine problems deciding that adding bad information to the data is worse than accepting that some information is missing.
# 
# If fixing these problems was imperative, I would attempt to train a supervised learning algorithm to try and harness more information than just the names in attempt to more accurately label the missing cuisine types. If I were to apply this strategy, I would look for more data than just the 213 nodes from the Oxford data set as it would be unlikely that out of 516 nodes, 213 labeled data would be able to generalise over the remaining 303.

# ## Loading the Data :

# In[12]:

# This snippet uses the process_map function from the case study data.py script. This process is idempotent and will 
# only load more data into MongoDB if any of the following happens:
#     - The number of records in the MongoDB collection matching the data_name variable has changed.
#     - The value of the data_name variable changes.
#     - The number of records in the OSM file matching data_name changes.

import data as data_processor
data = data_processor.process_map(OSMFILE, True)

from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client.oxford_england_sample
collection = getattr(db, data_name)

collection_count = collection.count()

# If the collection size dowsn't match the data size, load/reload the data.
if collection_count != len(data):
    if collection_count > 0:
        collection.drop()
    collection.insert_many(data)

collection_count = collection.count()
sample_record = collection.find_one()
print "Number of records in the {} MongoDB collection: {}".format(data_name, collection_count)
print "A sample record from the {} MongoDB collection: {}".format(data_name, sample_record)


# ## Overview of the data :

# In[13]:

# Size of the OSM and JSON files.
import os
def get_size_in_mb_of_relative_file(file_name):
    wd = get_ipython().magic(u'pwd')
    return os.stat(wd + '/' + file_name).st_size / 1000.0 / 1000.0

for file_name in [OSMFILE, OSMFILE + '.json']:
    file_size = get_size_in_mb_of_relative_file(file_name)
    print "{} is {} MB in size.".format(file_name, file_size)


# In[14]:

# Number of records:
print "Number of records in the {} MongoDB collection: {}".format(data_name, collection_count)


# In[15]:

# Number of nodes:
num_nodes = collection.find({"type":"node"}).count()
print "Number of 'node' records in the {} MongoDB collection: {}".format(data_name, num_nodes)


# In[16]:

# Number of ways:
num_ways = collection.find({"type":"way"}).count()
print "Number of 'way' records in the {} MongoDB collection: {}".format(data_name, num_ways)


# In[17]:

# Number of unique users:
num_unique_users = len(collection.distinct("created.user"))
print "Number of unique 'users' in the {} MongoDB collection: {}".format(data_name, num_unique_users)


# In[18]:

# Number of unique amenity types:
num_unique_amenities = len(collection.distinct("amenity"))
print "Number of unique 'amenity' values in the {} MongoDB collection: {}".format(data_name, num_unique_amenities)


# In[19]:

# Number of unique cuisine types:
num_unique_cuisines = len(collection.distinct("cuisine"))
print "Number of unique 'cuisine' values in the {} MongoDB collection: {}".format(data_name, num_unique_cuisines)


# In[20]:

# Number of universities and colleges:
num_colleges = collection.find({"amenity": {"$in": ["university", "college"]}}).count()
print "Number of 'university' and 'college' records in the {} MongoDB collection: {}".format(data_name, num_colleges)


# ## Other interesting facts about the datasets :

# Oxford is a very interesting city not simply because of the history and prestige of Oxford University, but also because of its density and diversity of amenities woven within a fabric of well integrated network of pedestrian, bicycle, and public transport routes. It would be very interesting to explore the relationships between these amenities and the various networks that allow people to move around the city.
# 
# The outcome of analysis could be very helpful in planning activities and events within the city as well as providing information about which parts of the city are likely to be busiest during the tourist season.
# 
# That said, the OSM data for Oxford may not make such an analysis very easy to undertake. For example, data about the bus and rail networks are encoded using the NAPTAN schema ([NAPTAN stands for National Public Transport Access Nodes](https://www.gov.uk/government/publications/national-public-transport-access-node-schema)) but this information does not always contain information about street names.

# In[21]:

print "A bus stop node without street information."
print collection.find_one({"naptan": {"$exists": 1}, "highway": "bus_stop"})
print "\n"
print "A bus stop node with street information."
print collection.find_one({"naptan.Street": {"$exists": 1}, "highway": "bus_stop"})


# ### The top 10 most common amenities :

# In[22]:

results = collection.aggregate([
        {"$match": {"amenity": {"$exists": 1}}}, 
        {"$group": {"_id": "$amenity", "count": {"$sum": 1}}}, 
        {"$sort": {"count": -1}}, 
        {"$limit": 10}
    ])
for result in results:
    print result


# ### The top 10 most common types of cuisine :
# 
# For food nodes where the cuisine is known.

# In[23]:

results = collection.aggregate([
        {"$match": {"cuisine": {"$exists": 1}}}, 
        {"$group": {"_id": "$cuisine", "count": {"$sum": 1}}}, 
        {"$sort": {"count": -1}}, 
        {"$limit": 10}
    ])
for result in results:
    print result


# ### Top 10 most commonly found places to eat :

# In[24]:

results = collection.aggregate([
        {"$match": {"amenity": {"$in": ["restaurant", "cafe", "pub", "bar", "fast_food", "delicatessen"]}}}, 
        {"$match": {"name": {"$exists": 1}}},
        {"$group": {
                "_id": "$name", 
                "amenity": {"$first": "$amenity"}, 
                "cuisine": {"$push": "$cuisine"}, 
                "count": {"$sum": 1}
            }},
        {"$project": {
                "_id": 0, 
                "count": 1, 
                "name": "$_id", 
                "type" : {"$concat": [
                        "$amenity", " - ", 
                        {"$ifNull": [{"$arrayElemAt": ["$cuisine", 0 ]}, "unknown cuisine"] }
                    ]}
            }},
        {"$sort": {"count": -1}}, 
        {"$limit": 10}
    ])

for result in results:
    print "Count {}: {} ({})".format(result['count'], result['name'], result['type'])


# It is interesting to note that Asian cuisines occupy 4 of the top top types of cuisine (1: Chinese, 3: Indian, 9: Thai, 1: Asian), yet there isn't a single business offering Asian cuisine in the top 10 most commonly found places to eat. This begins to illustrate the trend that even though business offering Asian cuisine are numerous, they tend to be independent establishments rather than franchises or chains.

# ### The total reported bicycle parking capacity :
# 
# We can't make any assumptions for records where 'capacity' is known.

# In[25]:

from bson.code import Code

result = collection.inline_map_reduce(
    Code("function() {"
         "    if (this.capacity) {"
         "        emit('total_bicycle_parking_capacity', Number(this.capacity));"
         "    }"
         "}"), 
    Code("function(key, values) {"
         "    var total = 0;"
         "    for (var i = 0; i < values.length; i++) {"
         "        total += values[i];"
         "    }"
         "    return total;"
         "}"),
    query = {"amenity": "bicycle_parking"});
result


# ### The 5 streets with the most bus stops :
# 
# For bus stop nodes where the street name is known.

# In[26]:

results = collection.aggregate([
        {"$match": {"naptan": {"$exists": 1}, "highway": "bus_stop"}},
        {"$group": {"_id": "$naptan.Street", "num_bus_stops": {"$sum": 1}}},
        {"$project": {"_id": 0, "num_bus_stops": 1, "street_name": "$_id"}},
        {"$sort": {"num_bus_stops": -1}}, 
        {"$limit": 5}
    ])
for result in results:
    print result


# ## Conclusion :

# I am pleasantly surprised to see just how much information about Oxford is encoded within the OSM data. That said, the inevitable nature of crowd sourced information is clearly present. There is quite a lot of inconsistency in the data (not all illustrated in this project) as well as records that do little more than act as meta information about the creation of the data itself (such as 'fixme' and 'note').

# In[27]:

meta_keys = [key for key in unique_key_names if 'fixme' in key.lower() or 'note' in key.lower()]
percentage = '%.2f' % (float(len(meta_keys)) / len(unique_key_names) * 100)
print "There are {} 'meta' tag key names making up {}% of all unique tag key names.".format(len(meta_keys), percentage)
print "\n"
print [key for key in unique_key_names if 'fixme' in key.lower() or 'note' in key.lower()]


# ### Other Ideas about additional improvement , their benifits and problems :
# 
# After this review of the data it’s obvious that the area Oxford is incomplete, though I believe it has been well cleaned for the purposes of this exercise. However, the improvement may bring about potential problems if it's not implemented correctly:
# 
# -  When we audit the data, it was very clear that although there are minor error caused by human input, the dataset is fairly well-cleaned. Considering there're hundreds of contributors for this map, there is a great numbers of human errors in this project. So, Gamifimation may impact the quality (veracity) of the data submitted from the contributors. We need to keep in mind that quality should always be considered more important than quantity when we try implementing the improvement.
# - If the difference between the highest score and the rest is too large, users may easily loose their interest. Therefore, we should implement it in such a way that the higher the score is, the harder it becomes to increase. 
# - Since OpenStreetMaps is an open source project, there're still a lot of areas left unexplored as people tend to focus on a certain key areas and left other part outdated. we can resolve this issue by cross-referencing/cross-validating missing data from other database like Google API. Since each node has a coordinate (lattitude & longtitude), this process is definitely do-able.
# - With a rough GPS data processor in place and working together with a more robust data processor similar to data.py, I think it would be possible to input great amount of cleaned data to OpenStreetMap.org.
# - There we may face some potential cost of implementation. The amount of effort to engineer all these processes and the cost of creating, auditing & maintaining these initiatives could be so overwhelm and require a dedicated team responsible for all these projects.

# ### Resources :

# The production of this project was aided by information found on the following website (various authors and contributors)
# 
# - [Udacity.com](udacity.com)
# - [Docs.MongoDB.com](docs.mongodb.com)
# - [API.MongoDB.com/python](api.mongodb.com/python)
# - [StackOverflow.com](stackoverflow.com)
# - [Mapzen](https://mapzen.com/data/metro-extracts/)
# - Sample project [Github Repo](https://github.com/lyvinhhung/Udacity-Data-Analyst-Nanodegree/blob/master/p3%20-%20Wrangle%20OpenStreetMap%20Data/P3%20-%20Data%20Wrangling%20with%20MongoDB.ipynb)
# - [Blog Ref-1](http://ghunt03.github.io/DAProjects/DAP03/index.html)
# - [Blog Ref-2](https://olegleyz.github.io/data_wrangling.html)

# In[ ]:



