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
		self._process( rawMazeLayout )

	def _process( self, rawMazeLayout ):
		for row, col in itertools.product( range( self.rows ), range( self.cols ) ):
			token = rawMazeLayout[ row ][ col ]
			cellWeight = 0
			if ':' in token:
				N, propertyString = token.split( ':' )
				cellWeight = int( N )
				self.propertyDict[ (row, col) ] = propertyString
			elif '*' in token:
				self.rawContentDict[ (row, col) ] = token
				pass
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
	'n' : (-1, 0), 's' : (1, 0), 'w' : (0, -1), 'e' : (0, 1)
	}
	horizontalOrVerticalMoves = set( horizontalOrVerticalMovementCode.keys() )

	# NORTH WEST, NORTH EAST, SOUTH WEST, SOUTH EAST
	diagonalMovementCode = {
	'nw': (-1, -1), 'ne': (-1, 1), 'sw': (1, -1), 'se': (1,  1)
	}
	diagonalMoves = set( diagonalMovementCode.keys() )

	oppositeDirectionDict = {
	'n' : 's', 's' : 'n', 'e' : 'w', 'w' : 'e'
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

class JumpingMaze:
	def __init__( self, mazeLayout, mazeName=None ):
		self.rows, self.cols = mazeLayout.dimensions()
		self.mazeLayout = mazeLayout
		self.mazeName = mazeName

		self.startCell, self.targetCell = (0, 0), (self.rows - 1, self.cols - 1)
		self.allowedMovementCodes = Movement.horizontalOrVerticalMovementCode

	def __repr__( self ):
		return '{}:{} {} x {}'.format( self.__class__.__name__, self.mazeName, self.rows, self.cols )

	def _isCellOutsideGrid( self, cell ):
		row, col = cell
		return row < 0 or row >= self.rows or col < 0 or col >= self.cols

	def _getAllowedMoves( self, currentState ):
		return set( self.allowedMovementCodes.keys() )

	def _getStepCount( self, currentState ):
		row, col = currentState.cell
		return self.mazeLayout.getWeight( row, col )

	def _getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		allowedMoves = self._getAllowedMoves( currentState )
		stepCount = self._getStepCount( currentState )

		row, col = currentState.cell
		for directionTag, (du, dv) in self.allowedMovementCodes.items():
			if directionTag not in allowedMoves:
				continue
			adjacentCell = row + du * stepCount, col + dv * stepCount
			if self._isCellOutsideGrid( adjacentCell ):
				continue
			move = Move( moveCode=directionTag, moveDistance=stepCount )
			newSearchState = SearchState( adjacentCell, previousMove=move, previousState=currentState )
			adjacentStateList.append( newSearchState )
		return adjacentStateList

	def getDimensions( self ):
		return self.rows, self.cols

	def getMazeName( self ):
		return self.mazeName

	def setStartAndTargetCell( self, startCell, targetCell ):
		if not self._isCellOutsideGrid( startCell ) and not self._isCellOutsideGrid( targetCell ):
			self.startCell, self.targetCell = startCell, targetCell

	def _getCacheEntryFromSearchState( self, searchState ):
		return searchState.cell

	def solve( self ):
		initialState = SearchState( self.startCell, previousMove=None, previousState=None )

		q = deque()
		q.append( initialState )

		visited = set()
		visited.add( self._getCacheEntryFromSearchState( initialState ) )

		while len( q ) > 0:
			currentState = q.popleft()
			if currentState.isTargetCell( self.targetCell ):
				return currentState
			
			for adjacentState in self._getAdjacentStateList( currentState ):
				cacheEntry = self._getCacheEntryFromSearchState( adjacentState )
				if cacheEntry not in visited:
					visited.add( cacheEntry )
					q.append( adjacentState )
		return None

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

class JumpingMazeDiagonal( JumpingMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMaze.__init__( self, mazeLayout, mazeName )

		allowedMovementCodes = copy.deepcopy( Movement.horizontalOrVerticalMovementCode )
		allowedMovementCodes.update( Movement.diagonalMovementCode )
		self.allowedMovementCodes = allowedMovementCodes

	def _allowedMoves( self, moveType ):
		return Movement.horizontalOrVerticalMoves if moveType == Move.MOVE_TYPE_HORIZONTAL_OR_VERTICAL else \
		       Movement.diagonalMoves

class JumpingMazeSwitchDiagonal( JumpingMazeDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMazeDiagonal.__init__( self, mazeLayout, mazeName )

	def _getCacheEntryFromSearchState( self, searchState ):
		previousMoveType = None
		if searchState.previousMove is not None:
			previousMoveType = searchState.previousMove.moveType()
		return (searchState.cell, previousMoveType)

	def _getAllowedMoves( self, searchState ):
		if searchState.previousMove is None:
			return Movement.horizontalOrVerticalMoves
		else:
			return self._allowedMoves( searchState.previousMove.flipMoveType() )

class JumpingMazeToggleDirection( JumpingMazeDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMazeDiagonal.__init__( self, mazeLayout, mazeName )

		self.circleCellProperty = 'C'

	def _getCacheEntryFromSearchState( self, searchState ):
		previousMoveType = None
		if searchState.previousMove is not None:
			previousMoveType = searchState.previousMove.moveType()
		return (searchState.cell, previousMoveType)

	def _getAllowedMoves( self, searchState ):
		row, col = searchState.cell
		propertyString = self.mazeLayout.getPropertyString( row, col )

		if searchState.previousMove is None:
			return Movement.horizontalOrVerticalMoves
		elif propertyString == self.circleCellProperty:
			return self._allowedMoves( searchState.previousMove.flipMoveType() )
		else:
			return self._allowedMoves( searchState.previousMove.moveType() )

class JumpingMazeNoUTurn( JumpingMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMaze.__init__( self, mazeLayout, mazeName )

	def _getCacheEntryFromSearchState( self, searchState ):
		moveCode = None
		if searchState.previousMove is not None:
			moveCode = searchState.previousMove.moveCode
		return (searchState.cell, moveCode)

	def _getAllowedMoves( self, searchState ):
		if searchState.previousMove is None:
			return Movement.horizontalOrVerticalMoves
		moveCode = searchState.previousMove.moveCode
		return set.difference( Movement.horizontalOrVerticalMoves, [ Movement.oppositeDirectionDict[ moveCode ] ] )

class JumpingMazeWildcard( JumpingMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMaze.__init__( self, mazeLayout, mazeName )

		self.wildCardCell = '*'

	def _getCacheEntryFromSearchState( self, searchState ):
		previousCell = None
		if searchState.previousState is not None:
			previousCell = searchState.previousState.cell
		return (searchState.cell, previousCell)

	def _getStepCount( self, currentState ):
		row, col = currentState.cell
		rawContent = self.mazeLayout.getRaw( row, col )
		if rawContent == self.wildCardCell:
			return currentState.previousMove.moveDistance
		return self.mazeLayout.getWeight( row, col )

class JumpingMazeTest( unittest.TestCase ):
	def _verifyMaze( self, maze ):
		expectedPathList = readMazeSolutionFromFile( maze.getMazeName() )

		searchState = maze.solve()
		pathString, pathList = maze.getPath( searchState )

		print( maze )
		print( 'Path: {}'.format( pathString ) )
		print( 'Cell list: {}'.format( pathList ) )
		self.assertEqual( pathList, expectedPathList )
		print()

	def test_solve( self ):
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

		for mazeName in ('Grumble', 'DNA', 'Countdown', 'Transverse', 'Asterisks'):
			self._verifyMaze( JumpingMazeWildcard( readMazeFromFile( mazeName ), mazeName=mazeName ) )

if __name__ == '__main__':
	unittest.main()