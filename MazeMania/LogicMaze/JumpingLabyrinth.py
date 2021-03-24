import unittest
import os
from pathlib import Path
import itertools

from StateSpaceSearch import (StateSpaceSearch, Maze, MazeLayout, SearchState, Movement, Move)

class JumpingLabyrinth( StateSpaceSearch, Maze ):
	def __init__( self, mazeLayout, constraintList, mazeName=None ):
		Maze.__init__( self, mazeLayout, mazeName )
		
		self.allowedMovementCodes = Movement.horizontalOrVerticalMovementCode
		self.emptyCellToken, self.blockedCellToken, self.startCellToken, self.targetCellToken = '.', '#', 'S', 'T'
		self.blockedCells = set()

		rows, cols = self.getDimensions()
		for row, col in itertools.product( range( rows ), range( cols ) ):
			token = self.mazeLayout.getRaw( row, col )
			if token == self.startCellToken:
				self.startCell = (row, col)
			elif token == self.targetCellToken:
				self.targetCell = (row, col)
			elif token == self.blockedCellToken:
				self.blockedCells.add( (row, col) )
			else:
				assert token == self.emptyCellToken

		# For a given jump length, we store the next allowed jump length in self.distanceDict.
		self.distanceDict = dict()
		for i in range( len( constraintList ) ):
			self.distanceDict[ constraintList[ i ] ] = constraintList[ ( i + 1 ) % len( constraintList ) ]
		# Initial jump length is stored in self.distanceDict[ None ].
		self.distanceDict[ None ] = constraintList[ 0 ]

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		distance = self.distanceDict[ None ] if currentState.previousMove is None else \
		           self.distanceDict[ currentState.previousMove.moveDistance ]

		row, col = currentState.cell
		for directionTag, (du, dv) in self.allowedMovementCodes.items():
			# We have to move 'distance' units in the given direction. Each cell in our direction of
			# movement should be unblocked and inside the maze.
			for delta in range( 1, distance + 1 ):
				newCell = u, v = row + du * delta, col + dv * delta
				if self.isCellOutsideGrid( newCell ) or newCell in self.blockedCells:
					newCell = None
					break
			if newCell is not None:
				move = Move( moveCode=directionTag, moveDistance=distance )
				newSearchState = SearchState( newCell, previousMove=move, previousState=currentState )
				adjacentStateList.append( newSearchState )
		
		return adjacentStateList

	def getCacheEntryFromSearchState( self, searchState ):
		return (searchState.cell, None if searchState.previousMove is None else searchState.previousMove.moveDistance)

	def getStartState( self ):
		return SearchState( self.startCell, previousMove=None, previousState=None )

	def isTargetState( self, currentState ):
		return currentState.isTargetCell( self.targetCell )

	def solve( self ):
		searchState = self.breadthFirstSearch()
		pathString, _ = self.getPath( searchState )

		return pathString

class JumpingLabyrinthTest( unittest.TestCase ):
	def _readMaze( self, filename ):
		dataChunkList = list()
		with open( 'tests/JumpingLabyrinth/{}'.format( filename ) ) as inputFile:
			for inputLine in inputFile.readlines():
				dataChunkList.append( inputLine.strip() )
		mazeLayout = dataChunkList[ : -1 ]
		constraintList = list( map( int, dataChunkList[ -1 ].split( ',' ) ) )
		return mazeLayout, constraintList

	def _render( self, mazeLayout, mazeName, pathString, pathLength ):
		print( 'JumpingLabyrinth: mazeName = {}'.format( mazeName ) )
		for mazeRow in mazeLayout:
			print( mazeRow )
		prettyPathString = ''.join( map( lambda token : token.strip(), pathString.split( ':' ) ) )
		print( 'Path : {} Length = {}'.format( prettyPathString, pathLength ) )
		print()

	def _verify( self, testcaseFile, expectedSolutionDict ):
		mazeLayout, constraintList = self._readMaze( testcaseFile )
		mazeName = testcaseFile
		jumpingLabyrinth = JumpingLabyrinth( MazeLayout( mazeLayout ), constraintList, mazeName=mazeName )
		pathString = jumpingLabyrinth.solve()

		pathLength = len( pathString.split( ':' ) )
		self._render( mazeLayout, mazeName, pathString, pathLength )

		self.assertEqual( pathLength, expectedSolutionDict[ testcaseFile ] )

	def _readSolutionFile( self, solutionFileName ):
		expectedSolutionDict = dict()
		with open( 'tests/JumpingLabyrinth/{}.ans'.format( solutionFileName ) ) as solutionFile:
			for solutionLine in solutionFile.readlines():
				testcaseFile, expectedMoveCount = solutionLine.strip().split( ':' )
				expectedSolutionDict[ testcaseFile.strip() ] = int( expectedMoveCount )
		return expectedSolutionDict

	def test_solve( self ):
		testcaseFiles = set()
		for testcaseFile in os.listdir( 'tests/JumpingLabyrinth' ):
			testcaseFiles.add( Path( testcaseFile ).stem )

		solutionFileName = 'Solution'
		testcaseFiles.remove( solutionFileName )
		expectedSolutionDict = self._readSolutionFile( solutionFileName )
		
		for testcaseFile in testcaseFiles:
			self._verify( testcaseFile, expectedSolutionDict )

if __name__ == '__main__':
	unittest.main()