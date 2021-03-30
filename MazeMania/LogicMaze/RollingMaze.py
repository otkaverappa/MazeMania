import unittest
import os
from pathlib import Path
import itertools
import functools

from StateSpaceSearch import (StateSpaceSearch, Maze, MazeLayout, SearchState, Movement, Move,
	                          BaseMazeInterface, BlockOrientation)

class RollingBlock:
	def __init__( self, occupiedCells ):
		self.occupiedCells = occupiedCells

	def cells( self ):
		raise NotImplementedError()

	def move( self, directionTag ):
		raise NotImplementedError()

	def getOrientation( self ):
		raise NotImplementedError()

class RollingBlock_2_1_1( RollingBlock ):
	movementInfoDict = {
		(BlockOrientation.VERTICAL, 'N') : ((-2, 0, 0), (-1, 0, -1)),
		(BlockOrientation.VERTICAL, 'S') : (( 1, 0, 0), ( 2, 0, -1)),
		(BlockOrientation.VERTICAL, 'E') : (( 0, 1, 0), ( 0, 2, -1)),
		(BlockOrientation.VERTICAL, 'W') : (( 0,-2, 0), ( 0,-1, -1)),

		(BlockOrientation.HORIZONTAL_EAST_WEST, 'N') : ((-1, 0, 0), (-1, 0, 0)),
		(BlockOrientation.HORIZONTAL_EAST_WEST, 'S') : (( 1, 0, 0), ( 1, 0, 0)),
		(BlockOrientation.HORIZONTAL_EAST_WEST, 'E') : (( 0, 2, 0), ( 0, 1, 1)),
		(BlockOrientation.HORIZONTAL_EAST_WEST, 'W') : (( 0,-1, 0), ( 0,-2, 1)),


		(BlockOrientation.HORIZONTAL_NORTH_SOUTH, 'E') : ((0,  1, 0), ( 0, 1, 0)),
		(BlockOrientation.HORIZONTAL_NORTH_SOUTH, 'W') : ((0, -1, 0), ( 0,-1, 0)),
		(BlockOrientation.HORIZONTAL_NORTH_SOUTH, 'N') : ((-1, 0, 0), (-2, 0, 1)),
		(BlockOrientation.HORIZONTAL_NORTH_SOUTH, 'S') : (( 2, 0, 0), ( 1, 0, 1))
	}

	def __init__( self, occupiedCells ):
		assert len( occupiedCells ) == 2
		RollingBlock.__init__( self, occupiedCells )

	def cells( self ):
		return [ (r, c) for (r, c, _ ) in self.occupiedCells ]

	def move( self, directionTag ):
		orientation = self.getOrientation()
		(r1, c1, z1), (r2, c2, z2) = self.occupiedCells
		(du1, dv1, dw1), (du2, dv2, dw2) = RollingBlock_2_1_1.movementInfoDict[ (orientation, directionTag) ]

		cell1, cell2 = (r1 + du1, c1 + dv1, z1 + dw1), (r2 + du2, c2 + dv2, z2 + dw2)
		occupiedCells = (cell1, cell2)
		return RollingBlock_2_1_1( occupiedCells )

	def getOrientation( self ):
		(r1, c1, z1), (r2, c2, z2) = self.occupiedCells
		if (r1, c1) == (r2, c2):
			assert (z1, z2) == (0, 1)
			return BlockOrientation.VERTICAL
		elif r1 == r2:
			assert (z1, z2) == (0, 0) and c1 + 1 == c2
			return BlockOrientation.HORIZONTAL_EAST_WEST
		else:
			assert c1 == c2 and (z1, z2) == (0, 0) and r1 + 1 == r2
			return BlockOrientation.HORIZONTAL_NORTH_SOUTH

	def isTargetState( self, targetState ):
		return self.occupiedCells == targetState

class RollingBlockSearchState( SearchState ):
	def __init__( self, previousMove, previousState, rollingBlock ):
		SearchState.__init__( self, cell=None, previousMove=previousMove, previousState=previousState )
		self.rollingBlock = rollingBlock

	def isTargetState( self, targetState ):
		return self.rollingBlock.isTargetState( targetState )

class RollingBlockMaze( StateSpaceSearch, BaseMazeInterface ):
	def __init__( self, mazeLayout, mazeName=None ):
		rows, cols = len( mazeLayout ), len( mazeLayout[ 0 ] )
		BaseMazeInterface.__init__( self, rows, cols )

		self.mazeLayout = mazeLayout
		self.startCellToken, self.targetCellToken, self.emptyCellToken, self.blockedCellToken = 'S', 'T', '.', '#'
		
		self.startCellList = list()
		self.targetCellList = list()

		self.populateStartAndTargetCellList()

		self.allowedMoves = Movement.horizontalOrVerticalMoves
		self.adjacentStateFilterFunc = lambda currentState, newSearchState : True

		self.targetState = self.getTargetStateRollingBlock()

	def populateStartAndTargetCellList( self ):
		for row, col in itertools.product( range( self.rows ), range( self.cols ) ):
			if self.mazeLayout[ row ][ col ] == self.startCellToken:
				self.startCellList.append( (row, col) )
			elif self.mazeLayout[ row ][ col ] == self.targetCellToken:
				self.targetCellList.append( (row, col) )

	def applyMoves( self, directionTagList ):
		rollingBlock = self.getStartStateRollingBlock()
		for directionTag in directionTagList:
			newRollingBlock = rollingBlock.move( directionTag )
			if not all( map( self.isCellEmpty, newRollingBlock.cells() ) ):
				return False
			rollingBlock = newRollingBlock
		return rollingBlock.isTargetState( self.targetState )

	def isCellEmpty( self, cell ):
		row, col = cell
		return not self.isCellOutsideGrid( cell ) and not self.mazeLayout[ row ][ col ] == self.blockedCellToken

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()		

		for directionTag in self.allowedMoves:
			newRollingBlock = currentState.rollingBlock.move( directionTag )
			if all( map( self.isCellEmpty, newRollingBlock.cells() ) ):
				# All cells occupied by newRollingBlock are empty, which indicates that a move is possible.
				move = Move( moveCode=directionTag, moveDistance=None )
				newSearchState = RollingBlockSearchState( previousMove=move, previousState=currentState, rollingBlock=newRollingBlock )
				adjacentStateList.append( newSearchState )
		return filter( functools.partial( self.adjacentStateFilterFunc, currentState ), adjacentStateList )

	def getCacheEntryFromSearchState( self, searchState ):
		return searchState.rollingBlock.occupiedCells

	def getOccupiedCells( self, cellList ):
		N = len( cellList )
		assert N in (1, 2)
		
		# N = 1 for vertical orientation, and 2 for horizontal orientation.
		
		cellList.sort()
		if N == 1:
			x, y = cellList[ -1 ]
			cell1, cell2 = (x, y, 0), (x, y, 1)
		else:
			(x1, y1), (x2, y2) = cellList
			cell1, cell2 = (x1, y1, 0), (x2, y2, 0)
		return (cell1, cell2)

	def getStartStateRollingBlock( self ):
		return RollingBlock_2_1_1( self.getOccupiedCells( self.startCellList ) )

	def getTargetStateRollingBlock( self ):
		return self.getOccupiedCells( self.targetCellList )

	def getStartState( self ):
		rollingBlock = self.getStartStateRollingBlock()
		return RollingBlockSearchState( previousMove=None, previousState=None, rollingBlock=rollingBlock )

	def isTargetState( self, currentState ):
		return currentState.isTargetState( self.targetState )

	def solve( self ):
		searchState = self.breadthFirstSearch()
		pathString, _ = self.getPath( searchState, separator=str() )
		return pathString

	@staticmethod
	def read( mazeName, filePath ):
		rawMazeLayout = list()
		with open( filePath ) as inputFile:
			for inputLine in inputFile.readlines():
				rawMazeLayout.append( inputLine.strip() )
		return RollingBlockMaze( rawMazeLayout, mazeName )

class RollingBlockMazeColor( RollingBlockMaze ):
	def __init__( self, mazeLayout, mazeName, startCellId, targetCellId ):
		self.startCellId, self.targetCellId = startCellId, targetCellId
		
		RollingBlockMaze.__init__( self, mazeLayout, mazeName )

		def adjacentStateFilterFunc( currentState, newSearchState ):
			allCells = newSearchState.rollingBlock.cells()

			row, col = allCells[ 0 ]
			expectedColor = self.mazeLayout[ row ][ col ]
			return all( [ self.mazeLayout[ row ][ col ] == expectedColor for row, col in allCells ] )

		self.adjacentStateFilterFunc = adjacentStateFilterFunc

	def populateStartAndTargetCellList( self ):
		self.startCellList.append( self.convertCellNumber( self.startCellId ) )
		self.targetCellList.append( self.convertCellNumber( self.targetCellId ) )

	@staticmethod
	def read( mazeName, filePath ):
		rawMazeLayout = list()
		with open( filePath ) as inputFile:
			_, _, startCellId = inputFile.readline().strip().split()
			_, _, targetCellId = inputFile.readline().strip().split()
			for inputLine in inputFile.readlines():
				rawMazeLayout.append( inputLine.strip() )
		return RollingBlockMazeColor( rawMazeLayout, mazeName, int( startCellId ), int( targetCellId ) )

class RollingBlockMazeTest( unittest.TestCase ):
	def _readRollingBlockMazeSolution( self, mazeName ):
		with open( 'tests/RollingMaze/{}.ans'.format( mazeName ) ) as solutionFile:
			pathString = solutionFile.readline().strip()
		return pathString

	def test_RollingBlockMaze( self ):
		mazeNameList = [ 'RollingMaze{}'.format( i + 1 ) for i in range( 4 ) ]
		for mazeName in mazeNameList:
			filePath = 'tests/RollingMaze/{}'.format( mazeName )
			maze = RollingBlockMaze.read( mazeName, filePath )
			expectedPathString = self._readRollingBlockMazeSolution( mazeName )

			pathString = maze.solve()
			print( 'Maze = {} Path length = {} Path = {}'.format( mazeName, len( pathString ), pathString ) )
			self.assertEqual( len( pathString ), len( expectedPathString ) )
			if pathString != expectedPathString:
				self.assertEqual( maze.applyMoves( pathString ), True )

	def test_RollingBlockMazeColor( self ):
		mazeNameList = [ 'RollingMazeColor{}'.format( i + 1 ) for i in range( 10 ) ]
		for mazeName in mazeNameList:
			filePath = 'tests/RollingMaze/{}'.format( mazeName )
			maze = RollingBlockMazeColor.read( mazeName, filePath )
			#expectedPathString = self._readRollingBlockMazeSolution( mazeName )

			pathString = maze.solve()
			print( 'Maze = {} Path length = {} Path = {}'.format( mazeName, len( pathString ), pathString ) )

if __name__ == '__main__':
	unittest.main()