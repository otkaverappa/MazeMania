import unittest
from collections import deque
import itertools
import copy
import functools

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
		return currentState.isTargetState( self.targetCell )

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
		return currentState.isTargetState( self.targetCell )

	def solve( self ):
		return self.breadthFirstSearch()

class SequenceMove( Move ):
	def __init__( self, moveCode, moveDistance, sequenceCount=1 ):
		Move.__init__( self, moveCode, moveDistance )
		self.sequenceCount = sequenceCount
		self.shape = self.color = None
		self.matchType = None

class LinkMaze( StateSpaceSearch, Maze ):
	def __init__( self, mazeLayout, mazeName=None ):
		Maze.__init__( self, mazeLayout, mazeName )

		self.adjacentStateFilterFunc = lambda currentState, newSearchState : True
		self.allowedMovementCodes = copy.deepcopy( Movement.horizontalOrVerticalMovementCode )

		self.wildCardToken, self.emptyCellToken = '*', '.'
		self.circleCellToken = '*'

	def getColorProperty( self, row, col ):
		propertyString = self.mazeLayout.getPropertyString( row, col )
		if propertyString is not None:
			color, * _ = propertyString.split( '#' )
			return color
		return None

	def isCircled( self, row, col ):
		propertyString = self.mazeLayout.getPropertyString( row, col )
		return self.circleCellToken in propertyString

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		row, col = currentState.cell
		previousMove = currentState.previousMove

		shape, color = self.mazeLayout.getRaw( row, col ), self.getColorProperty( row, col )
		if shape == self.wildCardToken:
			shape, color = previousMove.shape, previousMove.color
		
		for directionTag, (du, dv) in self.allowedMovementCodes.items():
			distance = 1
			while True:
				adjacentCell = x, y = row + du * distance, col + dv * distance
				if self.isCellOutsideGrid( adjacentCell ):
					break
				newShape, newColor = self.mazeLayout.getRaw( x, y ), self.getColorProperty( x, y )
				isEmptyShape = newShape == self.emptyCellToken

				if isEmptyShape:
					break

				isWildcard = newShape == self.wildCardToken
				
				if isWildcard or newShape == shape or newColor == color:
					move = SequenceMove( moveCode=directionTag, moveDistance=distance )
					if previousMove is not None and previousMove.moveType() == move.moveType():
						move.sequenceCount = previousMove.sequenceCount + 1
					move.shape, move.color = shape, color
					move.matchType = (newShape == shape, newColor == color)
					newSearchState = SearchState( adjacentCell, previousMove=move, previousState=currentState )
					adjacentStateList.append( newSearchState )
				distance += 1

		return filter( functools.partial( self.adjacentStateFilterFunc, currentState ), adjacentStateList )

	def getCacheEntryFromSearchState( self, searchState ):
		return searchState.cell

	def getStartState( self ):
		return SearchState( self.startCell, previousMove=None, previousState=None )

	def isTargetState( self, currentState ):
		return currentState.isTargetState( self.targetCell )

	def solve( self ):
		return self.breadthFirstSearch()

class LinkMazeCacheCellMoveCode:
	def getCacheEntryFromSearchState( self, searchState ):
		moveCode = None
		if searchState.previousMove is not None:
			moveCode = searchState.previousMove.moveCode
		return (searchState.cell, moveCode)

class LinkMazeWildcard( LinkMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		LinkMaze.__init__( self, mazeLayout, mazeName )

	def getCacheEntryFromSearchState( self, searchState ):
		shape = color = None
		if searchState.previousMove is not None:
			shape, color = searchState.previousMove.shape, searchState.previousMove.color
		return (searchState.cell, shape, color)

def filterUTurnMove( currentState, newSearchState ):
	if currentState.previousState is None:
				return True
	previousMoveDirection = currentState.previousMove.moveCode
	currentMoveDirection = newSearchState.previousMove.moveCode
	return currentMoveDirection != Movement.oppositeDirectionDict[ previousMoveDirection ]

class LinkMazeNoUTurn( LinkMazeCacheCellMoveCode, LinkMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		LinkMaze.__init__( self, mazeLayout, mazeName )

		self.adjacentStateFilterFunc = filterUTurnMove

class LinkMazeAlternatePlainCircle( LinkMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		LinkMaze.__init__( self, mazeLayout, mazeName )

		def adjacentStateFilterFunc( currentState, newSearchState ):
			if currentState.previousState is None:
				return True
			x, y = currentState.cell
			currentCellCircled = self.isCircled( x, y )
			x, y = newSearchState.cell
			newCellCircled = self.isCircled( x, y )

			return currentCellCircled ^ newCellCircled

		self.adjacentStateFilterFunc = adjacentStateFilterFunc

class LinkMazeAlternateShapeColor( LinkMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		LinkMaze.__init__( self, mazeLayout, mazeName )

		def adjacentStateFilterFunc( currentState, newSearchState ):
			shapeMatch, colorMatch = newSearchState.previousMove.matchType
			if currentState.previousState is None:
				newSearchState.previousMove.matchType = (shapeMatch, False)
				return shapeMatch
			previousMoveShapeMatch, previousMoveColorMatch = currentState.previousMove.matchType
			if previousMoveShapeMatch and colorMatch:
				newSearchState.previousMove.matchType = (False, True)
				return True
			elif previousMoveColorMatch and shapeMatch:
				newSearchState.previousMove.matchType = (True, False)
				return True
			return False

		self.adjacentStateFilterFunc = adjacentStateFilterFunc

	def getCacheEntryFromSearchState( self, searchState ):
		shapeMatch = colorMatch = None
		if searchState.previousMove is not None:
			shapeMatch, colorMatch = searchState.previousMove.matchType
		return (searchState.cell, shapeMatch, colorMatch)

class LinkMazeSwitchShapeColor( LinkMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		LinkMaze.__init__( self, mazeLayout, mazeName )

		def adjacentStateFilterFunc( currentState, newSearchState ):
			shapeMatch, colorMatch = newSearchState.previousMove.matchType
			if currentState.previousState is None:
				newSearchState.previousMove.matchType = (shapeMatch, False)
				return shapeMatch
			x, y = currentState.cell
			currentCellCircled = self.isCircled( x, y )
			previousMoveShapeMatch, previousMoveColorMatch = currentState.previousMove.matchType

			assert previousMoveShapeMatch ^ previousMoveColorMatch == True
			
			if ( currentCellCircled and previousMoveShapeMatch ) or ( not currentCellCircled and previousMoveColorMatch ):
				newSearchState.previousMove.matchType = (False, colorMatch)
				return colorMatch
			else:
				newSearchState.previousMove.matchType = (shapeMatch, False)
				return shapeMatch

		self.adjacentStateFilterFunc = adjacentStateFilterFunc

	def getCacheEntryFromSearchState( self, searchState ):
		shapeMatch = colorMatch = None
		if searchState.previousMove is not None:
			shapeMatch, colorMatch = searchState.previousMove.matchType
		return (searchState.cell, shapeMatch)

class LinkMazeDiagonal( LinkMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		LinkMaze.__init__( self, mazeLayout, mazeName )
		self.allowedMovementCodes.update( Movement.diagonalMovementCode )

class LinkMazeSwitchDiagonalNoUTurn( LinkMazeCacheCellMoveCode, LinkMazeDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		LinkMazeDiagonal.__init__( self, mazeLayout, mazeName )

		def adjacentStateFilterFunc( currentState, newSearchState ):
			if currentState.previousState is None:
				return newSearchState.previousMove.moveCode in Movement.horizontalOrVerticalMovementCode
			
			previousMove, currentMove = currentState.previousMove, newSearchState.previousMove
			isMoveTypeSame = previousMove.moveType() == currentMove.moveType()
			previousMoveDirection = previousMove.moveCode
			currentMoveDirection = currentMove.moveCode
			if currentMoveDirection == Movement.oppositeDirectionDict[ previousMoveDirection ]:
				return False

			x, y = currentState.cell
			currentCellCircled = self.isCircled( x, y )
			return currentCellCircled ^ isMoveTypeSame

		self.adjacentStateFilterFunc = adjacentStateFilterFunc

class LinkMazeSwitchDiagonal( LinkMazeDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		LinkMazeDiagonal.__init__( self, mazeLayout, mazeName )
		self.maximumAllowedSequenceCount = 3
		self.allowedSequenceCountSet = set( [ (1, 2), (2, 3), (3, 1) ] )

		def adjacentStateFilterFunc( currentState, newSearchState ):
			# We should start from horizontal and vertical moves only.
			if currentState.previousState is None:
				return newSearchState.previousMove.moveCode in Movement.horizontalOrVerticalMovementCode
			A, B = currentState.previousMove.sequenceCount, newSearchState.previousMove.sequenceCount
			if B > self.maximumAllowedSequenceCount:
				return False
			return (A, B) in self.allowedSequenceCountSet

		self.adjacentStateFilterFunc = adjacentStateFilterFunc

	def getCacheEntryFromSearchState( self, searchState ):
		moveType = sequenceCount = None
		if searchState.previousMove is not None:
			moveType, sequenceCount = searchState.previousMove.moveType(), searchState.previousMove.sequenceCount
		return (searchState.cell, moveType, sequenceCount)

class ChessMaze( StateSpaceSearch, Maze ):
	def __init__( self, mazeLayout, mazeName=None ):
		Maze.__init__( self, mazeLayout, mazeName )

		adjacentCellList = list( Movement.horizontalOrVerticalMovementCode.values() )
		diagonalCellList = list( Movement.diagonalMovementCode.values() )
		
		# k : Knight, R : Rook, B : Bishop, K : King
		self.chessMovementCode = {
		'k' : { 'unit' : None,   'cellList' : [ (1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1) ] },
		'R' : { 'unit' : str(),  'cellList' : adjacentCellList },
		'B' : { 'unit' : str(),  'cellList' : diagonalCellList },
		'K' : { 'unit' : None,   'cellList' : adjacentCellList + diagonalCellList },
		'Q' : { 'unit' : str(),  'cellList' : adjacentCellList + diagonalCellList },
		}
		self.pawnToken = 'P'
		self.whitePieceToken = 'w'
		self.emptyCell = '*'
		self.adjacentStateFilterFunc = lambda currentState, newSearchState : True

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		row, col = currentState.cell
		currentPiece = self.mazeLayout.getRaw( row, col )
		if currentPiece == self.pawnToken:
			assert currentState.previousMove is not None
			currentPiece = currentState.previousMove.moveCode
		movementCodeDict = self.chessMovementCode[ currentPiece ]

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
			move = Move( moveCode=currentPiece, moveDistance=None )
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
						move = Move( moveCode=currentPiece, moveDistance=None )
						newSearchState = SearchState( adjacentCell, previousMove=move, previousState=currentState )
						adjacentStateList.append( newSearchState )
						break
		return filter( functools.partial( self.adjacentStateFilterFunc, currentState ), adjacentStateList )

	def getCacheEntryFromSearchState( self, searchState ):
		return searchState.cell

	def getStartState( self ):
		return SearchState( self.startCell, previousMove=None, previousState=None )

	def isTargetState( self, currentState ):
		return currentState.isTargetState( self.targetCell )

	def solve( self ):
		return self.breadthFirstSearch()

class ChessMazeDifferentColor( ChessMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		ChessMaze.__init__( self, mazeLayout, mazeName )
		self.greyPieceToken = 'g'

		# Compare the colors of the pieces in the currentState and newSearchState. Return True if they are
		# different.
		def adjacentStateFilterFunc( currentState, newSearchState ):
			row, col = currentState.cell
			color = self.mazeLayout.getPropertyString( row, col )
			self._verifyColor( color )

			u, v = newSearchState.cell
			adjacentCellColor = self.mazeLayout.getPropertyString( u, v )
			self._verifyColor( adjacentCellColor )

			return adjacentCellColor != color
		
		self.adjacentStateFilterFunc = adjacentStateFilterFunc

	def _verifyColor( self, color ):
		assert color in (None, self.whitePieceToken, self.greyPieceToken)

class ChessMazeFlipFlop( ChessMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		ChessMaze.__init__( self, mazeLayout, mazeName )

		def adjacentStateFilterFunc( currentState, newSearchState ):
			u, v = newSearchState.cell
			isWhitePiece = self.mazeLayout.getPropertyString( u, v ) == self.whitePieceToken
			if currentState.previousState is None:
				return not isWhitePiece
			x, y = currentState.cell
			isW1 = self.mazeLayout.getPropertyString( x, y ) == self.whitePieceToken
			x, y = currentState.previousState.cell
			isW2 = self.mazeLayout.getPropertyString( x, y ) == self.whitePieceToken
			if isW1 ^ isW2:
				return isWhitePiece == isW1
			else:
				return isWhitePiece != isW1

		self.adjacentStateFilterFunc = adjacentStateFilterFunc

	def getCacheEntryFromSearchState( self, searchState ):
		return (None if searchState.previousState is None else searchState.previousState.cell, searchState.cell)

class ChessMazeWildcard( ChessMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		ChessMaze.__init__( self, mazeLayout, mazeName )

	def getCacheEntryFromSearchState( self, searchState ):
		return (searchState.cell, searchState.previousMove.moveCode if searchState.previousMove is not None else None)

class CalculationSearchState( SearchState ):
	def __init__( self, cell, previousMove, previousState, accumulator ):
		SearchState.__init__( self, cell, previousMove, previousState )
		self.accumulator = accumulator

	def isTargetState( self, targetCell, targetAccumulatorValue ):
		return self.cell == targetCell and self.accumulator == targetAccumulatorValue

class CalculationMaze( StateSpaceSearch, Maze ):
	def __init__( self, mazeLayout, mazeName=None, target=0 ):
		Maze.__init__( self, mazeLayout, mazeName )
		
		self.targetAccumulatorValue = target

		self.allowedMovementCodes = copy.deepcopy( Movement.horizontalOrVerticalMovementCode )
		self.supportedSymbols = set( [ '=', '+', '-', 'x' ] )
		self.adjacentStateFilterFunc = lambda currentState, newSearchState: True

	def apply( self, token, accumulator ):
		# token is of the form: "=0", "+3", "-3", "x1"
		symbol, argument = token[ 0 ], int( token[ 1 : ] )
		assert symbol in self.supportedSymbols

		result = None
		if symbol == '=':
			result = argument
		elif symbol == '+':
			result = accumulator + argument
		elif symbol == '-':
			result = accumulator - argument
		elif symbol == 'x':
			result = accumulator * argument
		return result

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		row, col = currentState.cell
		accumulator = currentState.accumulator
		for directionTag, (du, dv) in self.allowedMovementCodes.items():
			adjacentCell = x, y = row + du, col + dv
			if self.isCellOutsideGrid( adjacentCell ):
				continue
			newAccumulator = self.apply( self.mazeLayout.getRaw( x, y ), accumulator )
			move = Move( moveCode=directionTag, moveDistance=1 )
			newSearchState = CalculationSearchState( adjacentCell, previousMove=move, previousState=currentState,
				                                     accumulator=newAccumulator )
			adjacentStateList.append( newSearchState )
		
		return filter( functools.partial( self.adjacentStateFilterFunc, currentState ), adjacentStateList )

	def getCacheEntryFromSearchState( self, searchState ):
		return (searchState.cell, searchState.accumulator)

	def getStartState( self ):
		return CalculationSearchState( self.startCell, previousMove=None, previousState=None, accumulator=0 )

	def isTargetState( self, currentState ):
		return currentState.isTargetState( self.targetCell, self.targetAccumulatorValue )

	def solve( self ):
		return self.breadthFirstSearch()

class CalculationMazeNoUTurn( CalculationMaze ):
	def __init__( self, mazeLayout, mazeName=None, target=0 ):
		CalculationMaze.__init__( self, mazeLayout, mazeName, target=target )

		self.adjacentStateFilterFunc = filterUTurnMove

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

	def test_CalculationMaze( self ):
		for mazeName, target in (('KeyToTheDoor', 21), ):
			self._verifyMaze( CalculationMaze( readMazeFromFile( mazeName ), mazeName=mazeName, target=target ) )

		for mazeName, target in (('TopTen', 10), ):
			self._verifyMaze( CalculationMazeNoUTurn( readMazeFromFile( mazeName ), mazeName=mazeName, target=target ) )

	def test_LinkMaze( self ):
		for mazeName in ('DaisyChain', 'Ladder'):
			self._verifyMaze( LinkMaze( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Skeetology', 'ThreeByThree'):
			self._verifyMaze( LinkMazeSwitchDiagonal( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Linkology', ):
			self._verifyMaze( LinkMazeWildcard( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		# Multiple solutions for Caterpillar
		for mazeName in ('Linkholes', 'Jingo', 'Jango', 'Slinky'):
			self._verifyMaze( LinkMazeAlternateShapeColor( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('MirrorMirror', ):
			self._verifyMaze( LinkMazeDiagonal( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Circulate', ):
			self._verifyMaze( LinkMazeAlternatePlainCircle( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('FlipFlop', ):
			self._verifyMaze( LinkMazeSwitchShapeColor( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Banana', 'DoubleDiamond'):
			self._verifyMaze( LinkMazeNoUTurn( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Miniminx', ):
			self._verifyMaze( LinkMazeSwitchDiagonalNoUTurn( readMazeFromFile( mazeName ), mazeName=mazeName ) )

	def test_ChessMaze( self ):
		for mazeName in ('FourKings', 'Chess77', 'BishopCastleKnight'):
			self._verifyMaze( ChessMaze( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		# Multiple solutions for ChessMoves and TheCastle.
		for mazeName in ('ChessMoves', ):
			pass

		for mazeName in ('KnightsCircle', 'ThreeKings', 'Whirlpool', 'KnightAndDay', 'TheCastle', 'Greyknights'):
			self._verifyMaze( ChessMazeDifferentColor( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Cuckoo', 'Chessopolis', 'Chameleon', 'Mimic', 'Chessmaster'):
			self._verifyMaze( ChessMazeWildcard( readMazeFromFile( mazeName ), mazeName=mazeName ) )

		for mazeName in ('Chesapeake', 'TreasureChess', 'TheDarkKnight'):
			self._verifyMaze( ChessMazeFlipFlop( readMazeFromFile( mazeName ), mazeName=mazeName ) )

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