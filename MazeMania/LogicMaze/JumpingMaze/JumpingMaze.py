import unittest
from collections import deque
import itertools

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
				pass
			else:
				cellWeight = int( token )
			self.mazeLayout[ row ][ col ] = cellWeight

	def getWeight( self, row, col ):
		return self.mazeLayout[ row ][ col ]

	def getPropertyString( self, row, col ):
		return self.propertyDict.get( (row, col) )

	def dimensions( self ):
		return self.rows, self.cols

class Movement:
	# NORTH, SOUTH, WEST, EAST
	horizontalMovementDelta = {
	'n' : (-1, 0), 's' : (1, 0), 'w' : (0, -1), 'e' : (0, 1)
	}
	horizontalMoves = set( horizontalMovementDelta.keys() )

	# NORTH WEST, NORTH EAST, SOUTH WEST, SOUTH EAST
	diagonalMovementDelta = {
	'nw': (-1, -1), 'ne': (-1, 1), 'sw': (1, -1), 'se': (1,  1)
	}
	diagonalMoves = set( diagonalMovementDelta.keys() )

class JumpingMaze:
	def __init__( self, mazeLayout, mazeName=None ):
		self.rows, self.cols = mazeLayout.dimensions()
		self.mazeLayout = mazeLayout
		self.mazeName = mazeName

		self.startCell, self.targetCell = (0, 0), (self.rows - 1, self.cols - 1)
		self.movementDelta = Movement.horizontalMovementDelta

	def __repr__( self ):
		return '{}:{} {} x {}'.format( self.__class__.__name__, self.mazeName, self.rows, self.cols )

	def _isCellOutsideGrid( self, cell ):
		row, col = cell
		return row < 0 or row >= self.rows or col < 0 or col >= self.cols

	def _getAllowedMoves( self, currentCell, stepCount, previousMove ):
		return set( self.movementDelta.keys() )

	def _getAdjacentStateList( self, currentCell, stepCount, previousMove=None ):
		adjacentCellList = list()

		allowedMoves = self._getAllowedMoves( currentCell, stepCount, previousMove )

		row, col = currentCell
		for directionTag, (du, dv) in self.movementDelta.items():
			if directionTag not in allowedMoves:
				continue
			adjacentCell = row + du * stepCount, col + dv * stepCount
			if self._isCellOutsideGrid( adjacentCell ):
				continue
			adjacentCellList.append( (directionTag, adjacentCell) )
		return adjacentCellList

	def getDimensions( self ):
		return self.rows, self.cols

	def getMazeName( self ):
		return self.mazeName

	def setStartAndTargetCell( self, startCell, targetCell ):
		if not self._isCellOutsideGrid( startCell ) and not self._isCellOutsideGrid( targetCell ):
			self.startCell, self.targetCell = startCell, targetCell

	def getStepCount( self, row, col ):
		return self.mazeLayout.getWeight( row, col )

	def _getCacheEntryFromState( self, cell, previousMove ):
		return cell

	def solve( self ):
		movementString = str()
		previousMove = None

		q = deque()
		q.append( (self.startCell, movementString, previousMove) )

		visited = set()
		visited.add( self._getCacheEntryFromState( self.startCell, previousMove ) )

		while len( q ) > 0:
			currentCell, movementString, previousMove = q.popleft()
			if currentCell == self.targetCell:
				return movementString
			row, col = currentCell
			stepCount = self.getStepCount( row, col )
			for directionTag, adjacentCell in self._getAdjacentStateList( currentCell, stepCount, previousMove ):
				newMovementString = movementString + ':' + directionTag if previousMove is not None else directionTag

				cacheEntry = self._getCacheEntryFromState( adjacentCell, directionTag )
				if cacheEntry not in visited:
					visited.add( cacheEntry )
					q.append( (adjacentCell, newMovementString, directionTag ) )
		return None

	def getPathCode( self, movementString ):
		def cellNumber( row, col ):
			return row * self.cols + col + 1

		currentRow, currentCol = self.startCell
		pathList = [ cellNumber( currentRow, currentCol ) ]
		
		for directionTag in movementString.split( ':' ):
			du, dv = self.movementDelta[ directionTag ]
			stepCount = self.mazeLayout.getWeight( currentRow, currentCol )
			currentRow, currentCol = currentRow + du * stepCount, currentCol + dv * stepCount
			pathList.append( cellNumber( currentRow, currentCol) )
		return pathList

class JumpingMazeDiagonal( JumpingMaze ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMaze.__init__( self, mazeLayout, mazeName )
		self.movementDelta.update( Movement.diagonalMovementDelta )

	def _moveType( self, move ):
		return 'HORIZONTAL' if move in Movement.horizontalMoves else 'DIAGONAL'

	def _flipMoveType( self, moveType ):
		return 'DIAGONAL' if moveType == 'HORIZONTAL' else 'HORIZONTAL'

	def _allowedMoves( self, moveType ):
		return Movement.horizontalMoves if moveType == 'HORIZONTAL' else Movement.diagonalMoves

class JumpingMazeSwitchDiagonal( JumpingMazeDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMazeDiagonal.__init__( self, mazeLayout, mazeName )

	def _getCacheEntryFromState( self, cell, previousMove ):
		return (cell, self._moveType( previousMove ) == 'HORIZONTAL')

	def _getAllowedMoves( self, currentCell, stepCount, previousMove ):
		if previousMove is None:
			return Movement.horizontalMoves
		else:
			return self._allowedMoves( self._flipMoveType( self._moveType( previousMove ) ) )

class JumpingMazeToggleDirection( JumpingMazeDiagonal ):
	def __init__( self, mazeLayout, mazeName=None ):
		JumpingMazeDiagonal.__init__( self, mazeLayout, mazeName )

		self.circleCellProperty = 'C'

	def _getCacheEntryFromState( self, cell, perviousMove ):
		return (cell, self._moveType( perviousMove ) == 'HORIZONTAL' )

	def _getAllowedMoves( self, currentCell, stepCount, previousMove ):
		row, col = currentCell
		propertyString = self.mazeLayout.getPropertyString( row, col )

		if previousMove is None:
			return Movement.horizontalMoves
		elif propertyString == self.circleCellProperty:
			return self._allowedMoves( self._flipMoveType( self._moveType( previousMove ) ) )
		else:
			return self._allowedMoves( self._moveType( previousMove ) )

class JumpingMazeTest( unittest.TestCase ):
	def _verifyMaze( self, maze ):
		expectedPathList = readMazeSolutionFromFile( maze.getMazeName() )

		pathString = maze.solve()
		pathList = maze.getPathCode( pathString )

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

if __name__ == '__main__':
	unittest.main()