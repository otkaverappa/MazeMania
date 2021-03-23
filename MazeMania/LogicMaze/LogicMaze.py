import unittest
from collections import deque
import itertools
import copy

def readMazeFromFile( filename ):
	rawMazeLayout = list()
	with open( 'tests/{}'.format( filename ) ) as inputFile:
		for inputLine in inputFile.readlines():
			rawMazeLayout.append( list( inputLine.strip().split() ) )
	return MazeLayout( rawMazeLayout )

def readMazeSolutionFromFile( filename ):
	with open( 'tests/{}.ans'.format( filename ) ) as solutionFile:
		return list( map( int, solutionFile.readline().split() ) )

class MazeLayout:
	def __init__( self, rawMazeLayout ):
		self.rows, self.cols = len( rawMazeLayout ), len( rawMazeLayout[ 0 ] )
		
		self.mazeLayout = [ [ None for _ in range( self.cols ) ] for _ in range( self.rows ) ]
		self.rawContentDict = dict()
		self.propertyDict = dict()
		self.specialTokens = set( [ '*', 'N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW' ] )
		self._process( rawMazeLayout )

	def _process( self, rawMazeLayout ):
		for row, col in itertools.product( range( self.rows ), range( self.cols ) ):
			token = rawMazeLayout[ row ][ col ]
			
			cellWeight = 0
			propertyString = None
			
			if ':' in token:
				token, propertyString = token.split( ':' )
			if propertyString is not None:
				self.propertyDict[ (row, col) ] = propertyString
			if token in self.specialTokens:
				self.rawContentDict[ (row, col) ] = token
			else:
				cellWeight = int( token )
			
			self.mazeLayout[ row ][ col ] = cellWeight

	def getRaw( self, row, col ):
		if (row, col) in self.rawContentDict:
			return self.rawContentDict[ (row, col) ]
		return self.mazeLayout[ row ][ col ]

	def getWeight( self, row, col ):
		return self.mazeLayout[ row ][ col ]

	def getPropertyString( self, row, col ):
		return self.propertyDict.get( (row, col) )

	def dimensions( self ):
		return self.rows, self.cols

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

	oppositeDirectionDict = {
	'N' : 'S', 'S' : 'N', 'E' : 'W', 'W' : 'E'
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
	def __init__( self, cell, previousMove, previousState ):
		self.cell = cell
		assert previousMove is None or isinstance( previousMove, Move )
		assert previousState is None or isinstance( previousState, SearchState )
		self.previousMove = previousMove
		self.previousState = previousState

	def isTargetCell( self, targetCell ):
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
		self.rows, self.cols = mazeLayout.dimensions()
		self.mazeLayout = mazeLayout
		self.mazeName = mazeName

		self.startCell, self.targetCell = (0, 0), (self.rows - 1, self.cols - 1)
		self.allowedMovementCodes = Movement.horizontalOrVerticalMovementCode

	def __repr__( self ):
		return '{}:{} {} x {}'.format( self.__class__.__name__, self.mazeName, self.rows, self.cols )

	def isCellOutsideGrid( self, cell ):
		row, col = cell
		return row < 0 or row >= self.rows or col < 0 or col >= self.cols

	def getDimensions( self ):
		return self.rows, self.cols

	def getMazeName( self ):
		return self.mazeName

	def getPath( self, searchState ):
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
		
		return ' : '.join( pathStringList ), cellList

class JumpingMaze( StateSpaceSearch, Maze ):
	def __init__( self, mazeLayout, mazeName=None ):
		Maze.__init__( self, mazeLayout, mazeName )

	def getAllowedMoves( self, currentState ):
		return set( self.allowedMovementCodes.keys() )

	def _defaultStepCount( self, currentState ):
		row, col = currentState.cell
		return self.mazeLayout.getWeight( row, col )

	def getStepCount( self, currentState ):
		return self._defaultStepCount( currentState )

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		allowedMoves = self.getAllowedMoves( currentState )
		try:
			stepCount = self.getStepCount( currentState )
		except UseDefaultImplementation:
			stepCount = self._defaultStepCount( currentState )

		row, col = currentState.cell
		for directionTag, (du, dv) in self.allowedMovementCodes.items():
			if directionTag not in allowedMoves:
				continue
			adjacentCell = row + du * stepCount, col + dv * stepCount
			if self.isCellOutsideGrid( adjacentCell ):
				continue
			move = Move( moveCode=directionTag, moveDistance=stepCount )
			newSearchState = SearchState( adjacentCell, previousMove=move, previousState=currentState )
			adjacentStateList.append( newSearchState )
		return adjacentStateList

	def setStartAndTargetCell( self, startCell, targetCell ):
		if not self.isCellOutsideGrid( startCell ) and not self.isCellOutsideGrid( targetCell ):
			self.startCell, self.targetCell = startCell, targetCell

	def getCacheEntryFromSearchState( self, searchState ):
		return searchState.cell

	def getStartState( self ):
		return SearchState( self.startCell, previousMove=None, previousState=None )

	def isTargetState( self, currentState ):
		return currentState.isTargetCell( self.targetCell )

	def solve( self ):
		return self.breadthFirstSearch()

class JumpingMazeDiagonal( JumpingMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMaze.__init__( self, mazeLayout, mazeName )

		allowedMovementCodes = copy.deepcopy( Movement.horizontalOrVerticalMovementCode )
		allowedMovementCodes.update( Movement.diagonalMovementCode )
		self.allowedMovementCodes = allowedMovementCodes

	def _allowedMoves( self, moveType ):
		return Movement.horizontalOrVerticalMoves if moveType == Move.MOVE_TYPE_HORIZONTAL_OR_VERTICAL else \
		       Movement.diagonalMoves

class SwitchMoveMixin:
	def getAllowedMoves( self, searchState ):
		if searchState.previousMove is None:
			return Movement.horizontalOrVerticalMoves
		else:
			return self._allowedMoves( searchState.previousMove.flipMoveType() )

class ToggleMoveMixin:
	circleCellProperty = 'C'

	def getAllowedMoves( self, searchState ):
		row, col = searchState.cell
		propertyString = self.mazeLayout.getPropertyString( row, col )

		if searchState.previousMove is None:
			return Movement.horizontalOrVerticalMoves
		elif propertyString == ToggleMoveMixin.circleCellProperty:
			return self._allowedMoves( searchState.previousMove.flipMoveType() )
		else:
			return self._allowedMoves( searchState.previousMove.moveType() )

class CacheCellPositionMoveTypeMixin:
	def getCacheEntryFromSearchState( self, searchState ):
		previousMoveType = None
		if searchState.previousMove is not None:
			previousMoveType = searchState.previousMove.moveType()
		return (searchState.cell, previousMoveType)

class JumpingMazeSwitchDiagonal( SwitchMoveMixin, CacheCellPositionMoveTypeMixin, JumpingMazeDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMazeDiagonal.__init__( self, mazeLayout, mazeName )

class JumpingMazeToggleDirection( ToggleMoveMixin, CacheCellPositionMoveTypeMixin, JumpingMazeDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMazeDiagonal.__init__( self, mazeLayout, mazeName )

class JumpingMazeNoUTurn( JumpingMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMaze.__init__( self, mazeLayout, mazeName )

	def getCacheEntryFromSearchState( self, searchState ):
		moveCode = None
		if searchState.previousMove is not None:
			moveCode = searchState.previousMove.moveCode
		return (searchState.cell, moveCode)

	def getAllowedMoves( self, searchState ):
		if searchState.previousMove is None:
			return Movement.horizontalOrVerticalMoves
		moveCode = searchState.previousMove.moveCode
		return set.difference( Movement.horizontalOrVerticalMoves, [ Movement.oppositeDirectionDict[ moveCode ] ] )

class WildCardMixin:
	wildCardCell = '*'

	def _isWildCardCell( self, searchState ):
		row, col = searchState.cell
		return self.mazeLayout.getRaw( row, col ) == WildCardMixin.wildCardCell

	def getStepCount( self, currentState ):
		if self._isWildCardCell( currentState ):
			return currentState.previousMove.moveDistance
		raise UseDefaultImplementation()

class JumpingMazeWildcard( WildCardMixin, JumpingMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMaze.__init__( self, mazeLayout, mazeName )

	def getCacheEntryFromSearchState( self, searchState ):
		previousMoveDistance = 0
		if self._isWildCardCell( searchState ):
			previousMoveDistance = searchState.previousMove.moveDistance
		return (searchState.cell, previousMoveDistance)

class CacheCellPositionMoveTypeMoveDistanceMixin:
	def getCacheEntryFromSearchState( self, searchState ):
		previousMoveType = None
		if searchState.previousMove is not None:
			previousMoveType = searchState.previousMove.moveType()
		previousMoveDistance = 0
		if self._isWildCardCell( searchState ):
			previousMoveDistance = searchState.previousMove.moveDistance
		return (searchState.cell, previousMoveType, previousMoveDistance)

class JumpingMazeToggleDiagonalWildcard( WildCardMixin, CacheCellPositionMoveTypeMoveDistanceMixin, JumpingMazeToggleDirection ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMazeToggleDirection.__init__( self, mazeLayout, mazeName )	

class JumpingMazeSwitchDiagonalWildcard( WildCardMixin, CacheCellPositionMoveTypeMoveDistanceMixin, JumpingMazeSwitchDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMazeSwitchDiagonal.__init__( self, mazeLayout, mazeName )

class ArrowMaze( StateSpaceSearch, Maze ):
	def __init__( self, mazeLayout, mazeName=None ):
		Maze.__init__( self, mazeLayout, mazeName )

		self.arrowMovementCode = copy.deepcopy( Movement.horizontalOrVerticalMovementCode )
		self.arrowMovementCode.update( Movement.diagonalMovementCode )

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		row, col = currentState.cell
		moveCode = self.mazeLayout.getRaw( row, col )
		du, dv = self.arrowMovementCode[ moveCode ] 
		
		distance = 1
		while True:
			adjacentCell = u, v = row + du * distance, col + dv * distance
			if self.isCellOutsideGrid( adjacentCell ):
				break
			move = Move( moveCode=moveCode, moveDistance=distance )
			newSearchState = SearchState( adjacentCell, previousMove=move, previousState=currentState )
			adjacentStateList.append( newSearchState )
			distance += 1
		return adjacentStateList

	def getCacheEntryFromSearchState( self, initialState ):
		return initialState.cell

	def getStartState( self ):
		return SearchState( self.startCell, previousMove=None, previousState=None )

	def isTargetState( self, currentState ):
		return currentState.isTargetCell( self.targetCell )

	def solve( self ):
		return self.breadthFirstSearch()

class MazeTest( unittest.TestCase ):
	def _verifyMaze( self, maze ):
		expectedPathList = readMazeSolutionFromFile( maze.getMazeName() )

		searchState = maze.solve()
		pathString, pathList = maze.getPath( searchState )

		print( maze )
		print( 'Path: {}'.format( pathString ) )
		print( 'Cell list: {}'.format( pathList ) )
		self.assertEqual( pathList, expectedPathList )
		print()

	def test_ArrowMaze( self ):
		for mazeName in ('ArrowTheorem', ):
			self._verifyMaze( ArrowMaze( readMazeFromFile( mazeName ), mazeName=mazeName ) )

	def test_JumpMaze( self ):
		for mazeName in ('ChainReaction', 'Hopscotch'):
			self._verifyMaze( JumpingMaze( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		mazeName = 'Diamond'
		maze = JumpingMazeDiagonal( readMazeFromFile( mazeName ), mazeName=mazeName )
		rows, cols = maze.getDimensions()
		startCell, targetCell = (0, cols // 2), (rows - 1, cols // 2)
		maze.setStartAndTargetCell( startCell, targetCell )
		self._verifyMaze( maze )

		for mazeName in ('Bumblebee', 'DizzyDiagonals'):
			self._verifyMaze( JumpingMazeDiagonal( readMazeFromFile( mazeName ), mazeName=mazeName ) )
		
		for mazeName in ('SwitchMiss', 'Horizon', 'OneTwoThree', 'Lightswitch'):
			self._verifyMaze( JumpingMazeSwitchDiagonal( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Twangle', 'Triangle', 'Tangle', 'Switchblade', 'Megaminx'):
			self._verifyMaze( JumpingMazeToggleDirection( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Reflex', 'Noun'):
			self._verifyMaze( JumpingMazeNoUTurn( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Grumble', 'DNA', 'Countdown', 'Transverse', 'Asterisks', 'Coriolis'):
			self._verifyMaze( JumpingMazeWildcard( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Kangaroo', ):
			self._verifyMaze( JumpingMazeToggleDiagonalWildcard( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Zig-Zag', ):
			self._verifyMaze( JumpingMazeSwitchDiagonalWildcard( readMazeFromFile( mazeName ), mazeName=mazeName ) )

if __name__ == '__main__':
	unittest.main()