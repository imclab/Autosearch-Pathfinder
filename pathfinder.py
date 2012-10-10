from math import *
from autosearch import *

PADDING = 5
PATH_WIDTH = 61 # Path width in meters
OFFSET = PATH_WIDTH / 2 # Offset of even rows
FIELD_BORDER = 20 # In meters, the closest the plane should ever get to the edge of the field

class PathFinder:	
	
	""" build_path
		Inputs: The width and height of the field in meters, and the map
				generated by AutoSearch
		Outputs: An array of GPS coordinates that the plane should go to """
	def build_path (self,autoSearch):
		self.width_meters = int(autoSearch.width_meters)
		self.height_meters = int(autoSearch.height_meters)

		self.array_height = int(self.height_meters/ PATH_WIDTH) + 1
		self.array_width = int(self.width_meters/ PATH_WIDTH) + 1
		print "There are ",self.array_height*self.array_height," nodes."
		print "Array width: ",self.array_width
		print "Array height: ",self.array_height
		self.autoSearch = autoSearch
		triangle_array = self.build_array() # break field into triangles
		adj_list = self.build_triangles(triangle_array) # build graph out of vertices
		path = self.make_path(adj_list) # make path out of graph
		self.create_image(path,autoSearch.array,'map_nofix.jpg')
		self.fix_path(path,autoSearch.array,autoSearch.perimeters, autoSearch.center)
		self.create_image(path,autoSearch.array,'map.jpg')
		self.create_file(path,autoSearch,'path.txt')
		self.create_image_from_file(autoSearch,autoSearch.array,'path.txt','filemap.jpg')
		return path
	
	""" build_array
		Inputs: A height and width of the field (in meters)
		Outputs: An array that corresponds to the field. """
	def build_array(self):
		result = [[0 for j in range(self.array_height)] for i in range(self.array_width)]
		# print "Array width: %d Array height %d"%(self.array_width,self.array_height)
		# print result
		assert(len(result[0]) == self.array_height)
		for j in range(self.array_height):
			for i in range(self.array_width):
				x,y = self.array_to_meters(i,j)
				if (self.is_in_field(x,y)):
					# print "i:",i,"j:",j
					result[i][j] = 1
				else:
					#print "i:",i,"j:",j
					result[i][j] = 0
		
		return result

	""" create_image
		Inputs: The path that the plane will travel.
		Outputs: An image that corresponds to the path,
		 		that can be overlayed over the autoSearch image. """
	def create_image(self, path, array,filename):

		y = 0
		x = 0
		image = Image.new("RGB", (len(array),len(array[0])))
		pix = image.load()
		draw = ImageDraw.Draw(image)
		for col in array:
			y=0
			for element in col:
				#print "X: ",x,"Y:",y,"MaxX:",len(array[0]),"MaxY:",len(array)
				if ( element == 0 ):
					pix[x,y] = (255,255,255)
				elif ( element == 1):
					pix[x,y] =(166,166,166)
				elif ( element == 2):
					pix[x,y] = (166,166,166)
				y+=1
			x+=1
		prev_node = None

		count = 0
		for node in path:
			if prev_node == None:
				prev_node = node
				continue
			start = (prev_node.x,prev_node.y)
			stop = (node.x,node.y)
			#for child in prev_node.children:
			#	if ( child != None and prev_node.j % 2 == 1):
			#		draw.line([start,(child.x,child.y)],'#00FF00')
			draw.line([start,stop],'#000000')
			draw.text(start,str(count),'#FF0000')
			prev_node = node
			count += 1
		draw.text(stop,str(count),'#FF0000')
		image.save(filename,'jpeg')

		#image.Save(filename)
		print "Done!"

	""" create_image_from_file
		Inputs: Autosearch, the autosearch map, file with the gps coordinates, and the filename of the resulting image
		Outputs: An image with the path overlayed on the map
	"""
	def create_image_from_file(self,autosearch,array,pathfile,imagefile):
		y = 0
		x = 0
		image = Image.new("RGB", (len(array),len(array[0])))
		pix = image.load()
		draw = ImageDraw.Draw(image)
		for col in array:
			y=0
			for element in col:
				#print "X: ",x,"Y:",y,"MaxX:",len(array[0]),"MaxY:",len(array)
				if ( element == 0 ):
					pix[x,y] = (255,255,255)
				elif ( element == 1):
					pix[x,y] =(166,166,166)
				elif ( element == 2):
					pix[x,y] = (166,166,166)
				y+=1
			x+=1
		path = open(pathfile,'r')
		prev_loc = None
		count = 0
		for coord in path:
			
			lat = float(coord[coord.find('(')+1:coord.find(',')])
			lon = float(coord[coord.find(',')+1:coord.find(')')])
			x,y = autosearch.gpsToArrayCoord(lat,lon)
			x = int(x)
			y = int(y)
			if ( prev_loc == None):
				prev_loc = (x,y)
				draw.text((x,y),str(count),'#FF0000')
			else:
				draw.line([prev_loc,(x,y)],'#000000')
				draw.text((x,y),str(count),'#FF0000')
				prev_loc = (x,y)
			count += 1
		path.close()
		image.save(imagefile,'jpeg')

	""" create_file
		Inputs: The path that the plane will travel, the autoSearch map,
			 	and the filename for writing GPS coordinates
		Outputs: Comma separated GPS coordinates
	"""
	def create_file(self,path,autosearch,filename):
		f = open(filename,'w')
		for node in path:
			gps = autosearch.arrayCoordToGps(node.x,node.y)
			f.write('(%f,%f),\n'%(gps[0],gps[1]))
		f.close()


	""" is_in_field
		Inputs: An array coordinate for the autosearch array
		Outputs: If a field segment within path_width / 2 return true.
				 Otherwise returns false """
	def is_in_field(self,x,y):
		return self.autoSearch.searchAround(x,y,PATH_WIDTH/2)
	
	""" fix_path
		Inputs: The path, the autoSearch map, and an array of the
				lines that make up the perimeter
		Outputs: None
		Effects: Moves all nodes so that they are inside the
				 searchable area """
	def fix_path(self,path,array,perimeters,center):
		for idx,node in enumerate(path):
			should_move = False
			for x_offset in range(-FIELD_BORDER,FIELD_BORDER):
				for y_offset in range(-FIELD_BORDER,FIELD_BORDER):
					x,y = self.array_to_meters(node.i,node.j)
					x += x_offset
					y += y_offset
					if ( x < 0 or x >= self.width_meters):
						continue
					if ( y < 0 or y >= self.height_meters):
						continue

					if array[x][y] == OUT_OF_BOUNDS:
						should_move = True

			if should_move:
				node.x,node.y = self.get_closest_valid_point((node.x,node.y),array,perimeters,center,idx)


	
	""" get_closest_valid_point
		Inputs: The coordinates of a node that is outside ot the AutoSearch map,
				the lines that make up the perimeter of the map, and the coordinates of
				the center of the map
		Outputs: The closest point on the map nearest to the node """
	def get_closest_valid_point(self,point,array,perimeters,center,index):

		length = 0
		new_location = None
		
		# for perimeter in perimeters:

		# 	ap = (perimeter[0],point)

		# 	x1 = perimeter[0][0] - perimeter[1][0] 
		# 	x2 = ap[0][0] - ap[1][0]
		# 	y1 = perimeter[0][1] - perimeter[1][1]
		# 	y2 = ap[0][1] - ap[1][1]

		# 	dot_product12 = x1 * x2 + y1 * y2
		# 	dot_product11 = x1 * x1 + y1 * y1
		# 	proj = (dot_product12 / dot_product11 * x1, dot_product12 / dot_product11 * y1)

		# 	resultant_vector = (0-proj[0]-x2, 0-proj[1]-y2)
		# 	resultant_vector_length = sqrt(pow(resultant_vector[0],2)+pow(resultant_vector[1],2))
		# 	final_point = (point[0]+(resultant_vector[0]*1.05),point[1]+(resultant_vector[1]*1.05))
			
		# 	print "Point: ",final_point
		# 	if len(array) > final_point[0] and len(array[0]) > final_point[1] and array[final_point[0]][final_point[1]] == 1:
		# 		if resultant_vector_length < length or length == 0:
		# 	   		length = resultant_vector_length
		# 	   		new_location = final_point
		
		# if new_location != None:
		# 	print "Moved %s to %s (tangent method)"%(point,new_location)
		# 	return (new_location[0]/PATH_WIDTH,new_location[1]/PATH_WIDTH)

		center_vector = (center[0]-point[0],center[1]-point[1])
		
		slope,fixed_point = 0,None

		if abs(center_vector[1]) > abs(center_vector[0]):
			if center[1] > point[1]:
				step = 1
			else:
				step = -1
			slope = center_vector[0]/center_vector[1]
			for y in range(point[1],int(center[1]),step):
				x = int(point[0] + slope * (y - point[1]))
				if x < 0 or x >= len(array) or y < 0 or y >= len(array[0]):
					continue
				if array[x][y] != 0:
					fixed_point = (x,y)
					break
		else:
			if center[0] > point[0]:
				step = 1
			else:
				step = -1
			slope = center_vector[1]/center_vector[0]
			for x in range(point[0],int(center[0]),step):
				y = int(point[1] + slope * (x - point[0]))
				if x < 0 or x >= len(array) or y < 0 or y >= len(array[0]):
					continue
				if array[x][y] != 0:
					fixed_point = (x,y)
					break

		if fixed_point != None:
			x,y = fixed_point
			slope = center_vector[1]/center_vector[0]
			offset_x = sqrt((FIELD_BORDER**2)/(1 + slope**2))
			if (x > center[0]):
				offset_x *= -1
			
			offset_y = offset_x * slope

			print "Node: %d Moved %s to %s (center method)"%(index,point,(x + offset_x,y + offset_y))
			return x + offset_x,y + offset_y
		else:
			print "Node: %d Failed to move point %s"%(index,point)
			return point


	""" array_to_gps
		Inputs: The index of an element in triangle_array
		Outputs: The meter coordinate of the center of the index """
	def array_to_meters (self,i,j):
		if ( j % 2 == 1 ):
			x = i * PATH_WIDTH + 2 * OFFSET
		else:
			x = i * PATH_WIDTH + OFFSET
		y = j * PATH_WIDTH + OFFSET
		return x,y

	""" array_to_gps
		Inputs: The index of an element in triangle_array
		Outputs: The GPS coordinate of the center of the index """
	def array_to_gps(self,i,j):
		x,y = self.array_to_meters(i,j)
		return self.autoSearch.arrayCoordToGps(x,y)
		
	""" build_triangles
		Inputs: The map array
		Outputs: An adjacency list """
	def build_triangles(self,triangle_array):
		
		children = []
		id = -1

		nodes = []
		for j in range(self.array_height):
			for i in range(self.array_width):
				if triangle_array[i][j] == 1:
					id += 1
					node = Node(i,j,id,self)
					nodes += [node]

		adj_list = AdjacencyList(nodes)

		for j in range(self.array_height):
			for i in range(self.array_width):

				node = adj_list.node_at(i,j)
				if ( triangle_array[i][j] == 0 or node == None ):
					continue
				else:
					children = [None for x in range(6)]
				
				odd_vertices = [(i-1,j),(i,j+1),(i+1,j+1),(i+1,j),(i+1,j-1),(i,j-1)]
				even_vertices = [(i-1,j),(i-1,j+1),(i,j+1),(i+1,j),(i,j-1),(i-1,j-1)]
				if ( j % 2 == 0):
					vertices = even_vertices
				else:
					vertices = odd_vertices
				for idx,(i_s,j_s) in enumerate(vertices):
					if ( j_s >= 0 and j_s < self.array_height and i_s >= 0 and i_s < self.array_width and triangle_array[i_s][j_s] == 1 ):
						children[idx] = adj_list.node_at(i_s,j_s)
				
				node.set_children(children)
		return adj_list
	
	""" make_path
		Inputs: The adjacency list
		Outputs: An array with GPS waypoints ordered in an efficient way """
	def make_path(self,adj_list):
		path = []
		
		for n in adj_list.arr:
			n.visited = False
		
		for n in adj_list.arr:
			if not n.visited:
				print "CALLING dfs"
				path += self.dfs(n,0)
		print [x.id for x in path]
		return path
		
	""" dfs (Depth First Search)
		Inputs: The node to start the search, and the optimal direction for the
				search
		Outputs: A path that hits unvisited nodes using the most optimal
				 direction """
	def dfs_recursive(self,node,direction):
		#print "visiting node",node
		should_continue = True
		if ( node.visited ):
			#print "Node visited already",node.id
			return []

		node.visited = True
		path = [node]
		while True in [n.visited for n in node.children if n != None]:
			# if not :
			# 	break
			# should_continue = False
			# for n in node.children:
			# 	if n != None and not n.visited:
			# 		should_continue = True
			# if not should_continue:
			# 	#"Break!"
			# 	break
			#print "found unvisited node",node.id
			
			try:
				best,new_direction = self.pick_best(node,direction)
			except PathFinishedException:
				break
			
			path += self.dfs(best,new_direction)
		return path
	
	def dfs(self,node,direction):

		path = []
		stack = []

		try:
			while True:
				if not node.visited:
					node.visited = True
					path.append(node)
				try:
					child,direction = self.pick_best(node,direction)
					stack.append(child)
					node = child
				except PathFinishedException:
					node = stack.pop()
		except IndexError:
			pass
		return path
		
	""" pick_best
		Picks the best node to go to after visiting a certain node
		Inputs:	The current node and direction
		Outputs: The best node to go from here, and the new direction """
	def pick_best(self,node,direction):
		for index in [(direction + offset) % 6 for offset in [-2,-1,0,1,2,3]]:
			if (node.children[index] != None and node.children[index].visited == False):
				#print node.children[x].visited,node.children[x].id
				#print "direction: ",direction," new direction: ",index
				return node.children[index], index
		raise PathFinishedException()
		
		# for i in range(4):
		# 	if ( node.children[(direction+i) % 6] == None ):
		# 		pass
		# 	elif ( node.children[(direction+i) % 6].visited == False ):
		# 		# print "Found unvisited node!"
		# 		return node.children[(direction+i) % 6], (direction+i) % 6
		# 	if ( node.children[(direction-i) % 6] == None ):
		# 		pass
		# 	elif ( node.children[(direction-i) % 6].visited == False ):
		# 		# print "Found unvsisted node!"
		# 		return node.children[(direction-i) % 6], (direction-i) % 6
		# # print "All nodes visited!"
		# raise PathFinishedException()
class Node:
	def __init__(self,i,j,id,pathfinder):
		self.i = i
		self.j = j
		self.id = id
		self.pathfinder = pathfinder
		self.x,self.y = self.pathfinder.array_to_meters(i,j)
		self.children = [None for x in range(6)]
	
	def set_children(self,children):
		self.children = children

	def __str__(self):
		return "ID: %d, I: %d, J: %d, X: %d, Y: %d, Children: %s\n"%(self.id,self.i,self.j,self.x,self.y,self.children)

	def __repr__(self):
		return "ID: %d, I: %d, J: %d, X: %d, Y: %d, Children: %s\n"%(self.id,self.i,self.j,self.x,self.y,[child.id for child in self.children if child != None])
		
class AdjacencyList:
	def __init__(self,array):
		self.arr = array
		
	def push(self,node):
		self.arr.append(node)
		
	def node_at(self,i,j):
		# print "Array length: %d, Index: %d" %(len(self.arr),y*self.width+x)
		for node in self.arr:
			if node.i == i and node.j == j:
				return node
		return None
	
	def __str__(self):
		return "Array: %s"%(self.arr)
	
	def __repr__(self):
		return "Array: %s"%(self.arr)

class PathFinishedException(Exception):
	pass

class NodeFixed(Exception):
	pass