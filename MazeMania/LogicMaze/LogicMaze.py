import unittest
from collections import deque
import itertools
import copy

from StateSpaceSearch import (StateSpaceSearch, Maze, MazeLayout, SearchState, Movement, Move, UseDefaultImplementation)

def readMazeFromFile( filename ):
	rawMazeLayout = list()
	with open( 'tests/LogicMaze/{}'.format( filename ) ) as inputFile:
		for inputLine in inputFile.readlines():
			rawMazeLayout.append( list( inputLine.strip().split() ) )
	return MazeLayout( rawMazeLayout )

def readMazeSolutionFromFile( filename ):
	with open( 'tests/LogicMaze/{}.ans'.format( filename ) ) as solutionFile:
		return list( map( int, solutionFile.readline().split() ) )

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

	def getCacheEntryFromSearchState( self, searchState ):
		return searchState.cell

	def getStartState( self ):
		return SearchState( self.startCell, previousMove=None, previousState=None )

	def isTargetState( self, currentState ):
		return currentState.isTargetCell( self.targetCell )

	def solve( self ):
		return self.breadthFirstSearch()

class ChessMaze( StateSpaceSearch, Maze ):
	def __init__( self, mazeLayout, mazeName=None ):
		Maze.__init__( self, mazeLayout, mazeName )

		adjacentCellList = [ (0, 1), (0, -1), ( 1, 0), (-1,  0) ]
		diagonalCellList = [ (1, 1), (1, -1), (-1, 1), (-1, -1) ]
		
		# k : Knight, R : Rook, B : Bishop, K : King
		self.chessMovementCode = {
		'k' : { 'unit' : None,   'cellList' : [ (1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1) ] },
		'R' : { 'unit' : str(),  'cellList' : adjacentCellList },
		'B' : { 'unit' : str(),  'cellList' : diagonalCellList },
		'K' : { 'unit' : None,   'cellList' : adjacentCellList + diagonalCellList },
		'Q' : { 'unit' : str(),  'cellList' : adjacentCellList + diagonalCellList }
		}
		self.emptyCell = '*'

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		row, col = currentState.cell
		movementCodeDict = self.chessMovementCode[ self.mazeLayout.getRaw( row, col ) ]

		unit = movementCodeDict[ 'unit' ]
		cellDeltaList = movementCodeDict[ 'cellList' ]

		exploreList = list()

		for du, dv in cellDeltaList:
			adjacentCell = u, v = row + du, col + dv
			if self.isCellOutsideGrid( adjacentCell ):
				continue
			if self.mazeLayout.getRaw( u, v ) == self.emptyCell:
				exploreList.append( (du, dv) )
				continue
			move = Move( moveCode=str(), moveDistance=None )
			newSearchState = SearchState( adjacentCell, previousMove=move, previousState=currentState )
			adjacentStateList.append( newSearchState )

		if unit is not None:
			for du, dv in exploreList:
				u, v = row, col
				while True:
					adjacentCell = u, v = u + du, v + dv
					if self.isCellOutsideGrid( adjacentCell ):
						break
					if self.mazeLayout.getRaw( u, v ) != self.emptyCell:
						move = Move( moveCode=str(), moveDistance=None )
						newSearchState = SearchState( adjacentCell, previousMove=move, previousState=currentState )
						adjacentStateList.append( newSearchState )
						break
		
		return adjacentStateList

	def getCacheEntryFromSearchState( self, searchState ):
		return searchState.cell

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

	def test_ChessMaze( self ):
		for mazeName in ('FourKings', 'Chess77', 'BishopCastleKnight'):
			self._verifyMaze( ChessMaze( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('ChessMoves', ):
			pass

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