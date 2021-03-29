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

	def isTargetState( self, targetCell ):
		(r1, c1, z1), (r2, c2, z2) = self.occupiedCells
		return (r1, c1) == (r2, c2) == targetCell

class RollingBlockSearchState( SearchState ):
	def __init__( self, previousMove, previousState, rollingBlock ):
		SearchState.__init__( self, cell=None, previousMove=previousMove, previousState=previousState )
		self.rollingBlock = rollingBlock

	def isTargetState( self, targetCell ):
		return self.rollingBlock.isTargetState( targetCell )

class RollingBlockMaze( StateSpaceSearch, BaseMazeInterface ):
	def __init__( self, mazeLayout, mazeName=None ):
		rows, cols = len( mazeLayout ), len( mazeLayout[ 0 ] )
		BaseMazeInterface.__init__( self, rows, cols )

		self.mazeLayout = mazeLayout
		self.startCellToken, self.targetCellToken, self.emptyCellToken, self.blockedCellToken = 'S', 'T', '.', '#'
		self.startCell = self.targetCell = None
		for row, col in itertools.product( range( rows ), range( cols ) ):
			if mazeLayout[ row ][ col ] == self.startCellToken:
				self.startCell = (row, col)
			elif mazeLayout[ row ][ col ] == self.targetCellToken:
				self.targetCell = (row, col)

		self.allowedMoves = Movement.horizontalOrVerticalMoves
		self.adjacentStateFilterFunc = lambda currentState, newSearchState : True

	def applyMoves( self, directionTagList ):
		rollingBlock = self.getStartStateRollingBlock()
		for directionTag in directionTagList:
			newRollingBlock = rollingBlock.move( directionTag )
			if not all( map( self.isCellEmpty, newRollingBlock.cells() ) ):
				return False
			rollingBlock = newRollingBlock
		return rollingBlock.isTargetState( self.targetCell )

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

	def getStartStateRollingBlock( self ):
		x, y = self.startCell
		# Initial orientation is vertical - hence the occupied cell list has two cells with
		# x and y positions equal to the startCell, but with z position equal to 0 and 1 respectively.
		cell1, cell2 = (x, y, 0), (x, y, 1)
		occupiedCells = (cell1, cell2)
		return RollingBlock_2_1_1( occupiedCells )

	def getStartState( self ):
		rollingBlock = self.getStartStateRollingBlock()
		return RollingBlockSearchState( previousMove=None, previousState=None, rollingBlock=rollingBlock )

	def isTargetState( self, currentState ):
		return currentState.isTargetState( self.targetCell )

	def solve( self ):
		searchState = self.breadthFirstSearch()
		pathString, _ = self.getPath( searchState, separator=str() )
		return pathString

class RollingBlockMazeColor( RollingBlockMaze ):
	def __init__( self, mazeLayout, mazeName, startCellId, targetCellId ):
		RollingBlockMaze.__init__( self, mazeLayout, mazeName )
		self.startCell = self.convertCellNumber( startCellId )
		self.targetCell = self.convertCellNumber( targetCellId )

		def adjacentStateFilterFunc( currentState, newSearchState ):
			allCells = newSearchState.rollingBlock.cells()

			row, col = allCells[ 0 ]
			expectedColor = self.mazeLayout[ row ][ col ]
			return all( [ self.mazeLayout[ row ][ col ] == expectedColor for row, col in allCells ] )

		self.adjacentStateFilterFunc = adjacentStateFilterFunc

	@classmethod
	def read( self, mazeName, filePath ):
		rawMazeLayout = list()
		with open( filePath ) as inputFile:
			_, _, startCellId = inputFile.readline().strip().split()
			_, _, targetCellId = inputFile.readline().strip().split()
			for inputLine in inputFile.readlines():
				rawMazeLayout.append( inputLine.strip() )
		return RollingBlockMazeColor( rawMazeLayout, mazeName, int( startCellId ), int( targetCellId ) )

class RollingBlockMazeTest( unittest.TestCase ):
	def _readRollingBlockMaze( self, mazeName ):
		rawMazeLayout = list()
		with open( 'tests/RollingMaze/{}'.format( mazeName ) ) as inputFile:
			for inputLine in inputFile.readlines():
				rawMazeLayout.append( inputLine.strip() )
		return rawMazeLayout

	def _readRollingBlockMazeSolution( self, mazeName ):
		with open( 'tests/RollingMaze/{}.ans'.format( mazeName ) ) as solutionFile:
			pathString = solutionFile.readline().strip()
		return pathString

	def test_RollingBlockMaze( self ):
		for mazeName in ('RollingMaze1', 'RollingMaze2', 'RollingMaze3', 'RollingMaze4'):
			mazeLayout = self._readRollingBlockMaze( mazeName )
			maze = RollingBlockMaze( self._readRollingBlockMaze( mazeName ), mazeName=mazeName )
			expectedPathString = self._readRollingBlockMazeSolution( mazeName )

			pathString = maze.solve()
			print( 'Maze = {} Path length = {} Path = {}'.format( mazeName, len( pathString ), pathString ) )
			self.assertEqual( len( pathString ), len( expectedPathString ) )
			if pathString != expectedPathString:
				self.assertEqual( maze.applyMoves( pathString ), True )

	def test_RollingBlockMazeColor( self ):
		mazeNameList = [ 'RollingMazeColor{}'.format( i + 1 ) for i in range( 9 ) ]
		for mazeName in mazeNameList:
			filePath = 'tests/RollingMaze/{}'.format( mazeName )
			maze = RollingBlockMazeColor.read( mazeName, filePath )
			#expectedPathString = self._readRollingBlockMazeSolution( mazeName )

			pathString = maze.solve()
			print( 'Maze = {} Path length = {} Path = {}'.format( mazeName, len( pathString ), pathString ) )

if __name__ == '__main__':
	unittest.main()