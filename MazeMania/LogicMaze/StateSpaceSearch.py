import itertools
from collections import deque

class BaseMazeInterface:
	def __init__( self, rows, cols ):
		self.rows, self.cols = rows, cols

	def getDimensions( self ):
		return self.rows, self.cols

	def isCellOutsideGrid( self, cell ):
		row, col = cell
		return row < 0 or row >= self.rows or col < 0 or col >= self.cols

	def convertCellNumber( self, cellNumber ):
		cellNumber = cellNumber - 1
		return (cellNumber // self.cols, cellNumber % self.cols)

	def getPath( self, searchState, separator=' : ' ):
		def cellNumber( cell ):
			row, col = cell
			return row * self.cols + col + 1

		pathStringList = list()
		cellList = list()
		
		while searchState is not None:
			if searchState.previousMove is not None:
				pathStringList.append( searchState.previousMove.moveCode )
			cellList.append( cellNumber( searchState.cell ) )
			searchState = searchState.previousState

		pathStringList.reverse()
		cellList.reverse()
		
		return separator.join( pathStringList ), cellList

class MazeLayout( BaseMazeInterface ):
	def __init__( self, rawMazeLayout ):
		rows, cols = len( rawMazeLayout ), len( rawMazeLayout[ 0 ] )
		BaseMazeInterface.__init__( self, rows, cols )
		
		self.mazeLayout = [ [ None for _ in range( self.cols ) ] for _ in range( self.rows ) ]
		self.propertyDict = dict()
		
		self._process( rawMazeLayout )

	def _process( self, rawMazeLayout ):
		for row, col in itertools.product( range( self.rows ), range( self.cols ) ):
			token = rawMazeLayout[ row ][ col ]
			
			propertyString = None
			
			if ':' in token:
				token, propertyString = token.split( ':' )
			if propertyString is not None:
				self.propertyDict[ (row, col) ] = propertyString
			self.mazeLayout[ row ][ col ] = token

	def getRaw( self, row, col ):
		return self.mazeLayout[ row ][ col ]

	def getWeight( self, row, col ):
		weight = 0
		try:
			weight = int( self.mazeLayout[ row ][ col ] )
		except:
			pass
		return weight

	def getPropertyString( self, row, col ):
		return self.propertyDict.get( (row, col) )

class BlockOrientation:
	HORIZONTAL_EAST_WEST = 0
	HORIZONTAL_NORTH_SOUTH = 1
	VERTICAL = 2

class Movement:
	# NORTH, SOUTH, WEST, EAST
	horizontalOrVerticalMovementCode = {
	'N' : (-1, 0), 'S' : (1, 0), 'W' : (0, -1), 'E' : (0, 1)
	}
	horizontalOrVerticalMoves = set( horizontalOrVerticalMovementCode.keys() )

	# NORTH WEST, NORTH EAST, SOUTH WEST, SOUTH EAST
	diagonalMovementCode = {
	'NW': (-1, -1), 'NE': (-1, 1), 'SW': (1, -1), 'SE': (1,  1)
	}
	diagonalMoves = set( diagonalMovementCode.keys() )

	# NO MOVEMENT
	noMovementCode = {
	'~' : (0, 0)
	}

	oppositeDirectionDict = {
	'N' : 'S', 'S' : 'N', 'E' : 'W', 'W' : 'E',
	'NW' : 'SE', 'SE' : 'NW', 'NE' : 'SW', 'SW' : 'NE'
	}

class Move:
	MOVE_TYPE_HORIZONTAL_OR_VERTICAL = 0
	MOVE_TYPE_DIAGONAL = 1

	def __init__( self, moveCode, moveDistance ):
		self.moveCode = moveCode
		self.moveDistance = moveDistance

	def moveType( self ):
		if self.moveCode in Movement.horizontalOrVerticalMoves:
			return Move.MOVE_TYPE_HORIZONTAL_OR_VERTICAL
		assert self.moveCode in Movement.diagonalMoves
		return Move.MOVE_TYPE_DIAGONAL

	def flipMoveType( self ):
		moveType = self.moveType()
		return Move.MOVE_TYPE_DIAGONAL if moveType == Move.MOVE_TYPE_HORIZONTAL_OR_VERTICAL else \
		       Move.MOVE_TYPE_HORIZONTAL_OR_VERTICAL

class SearchState:
	dummyCell = (0, 0)

	def __init__( self, cell, previousMove, previousState ):
		self.cell = SearchState.dummyCell if cell is None else cell
		assert previousMove is None or isinstance( previousMove, Move )
		assert previousState is None or isinstance( previousState, SearchState )
		self.previousMove = previousMove
		self.previousState = previousState

	def isTargetState( self, targetCell ):
		return self.cell == targetCell

class StateSpaceSearch:
	def getAdjacentStateList( self, currentState ):
		raise NotImplementedError()

	def getCacheEntryFromSearchState( self, initialState ):
		raise NotImplementedError()

	def getStartState( self ):
		raise NotImplementedError()

	def isTargetState( self, currentState ):
		raise NotImplementedError()

	def breadthFirstSearch( self ):
		initialState = self.getStartState()

		q = deque()
		q.append( initialState )

		visited = set()
		visited.add( self.getCacheEntryFromSearchState( initialState ) )
		
		while len( q ) > 0:
			currentState = q.popleft()
			if self.isTargetState( currentState ):
				return currentState
			
			for adjacentState in self.getAdjacentStateList( currentState ):
				cacheEntry = self.getCacheEntryFromSearchState( adjacentState )
				if cacheEntry not in visited:
					visited.add( cacheEntry )
					q.append( adjacentState )
		return None

class UseDefaultImplementation( Exception ):
	pass

class Maze:
	def __init__( self, mazeLayout, mazeName=None ):
		self.rows, self.cols = mazeLayout.getDimensions()
		self.mazeLayout = mazeLayout
		self.mazeName = mazeName

		self.startCell, self.targetCell = (0, 0), (self.rows - 1, self.cols - 1)
		self.allowedMovementCodes = Movement.horizontalOrVerticalMovementCode

	def __repr__( self ):
		return '{}:{} {} x {}'.format( self.__class__.__name__, self.mazeName, self.rows, self.cols )

	def isCellOutsideGrid( self, cell ):
		return self.mazeLayout.isCellOutsideGrid( cell )

	def getDimensions( self ):
		return self.mazeLayout.getDimensions()

	def getMazeName( self ):
		return self.mazeName

	def getPath( self, searchState ):
		return self.mazeLayout.getPath( searchState )