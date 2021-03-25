import unittest
import os
from pathlib import Path
import itertools

from StateSpaceSearch import (StateSpaceSearch, Maze, MazeLayout, SearchState, Movement, Move, BaseMazeInterface)

class Labyrinth( BaseMazeInterface, StateSpaceSearch ):
	def __init__( self, rows, cols, blockingCellList, mazeName=None ):		
		BaseMazeInterface.__init__( self, rows, cols )
		self.startCell = self.targetCell = None

		self.allowedMovementCodes =  Movement.horizontalOrVerticalMovementCode

		self.blockedMoves = set()

		for blockingCellInfo in blockingCellList:
			fromCellNumber, directionString = blockingCellInfo.split( ':' )
			u, v = self._convertCellNumber( int( fromCellNumber ) )
			for directionTag in directionString:
				du, dv = self.allowedMovementCodes[ directionTag ]
				x, y = u + du, v + dv
				# We cannot move from (u, v) to (x, y) and from (x, y) to (u, v).
				self.blockedMoves.add( (u, v, x, y) )
				self.blockedMoves.add( (x, y, u, v) )

	def _convertCellNumber( self, cellNumber ):
		cellNumber = cellNumber - 1
		return (cellNumber // self.cols, cellNumber % self.cols)

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()

		for directionTag, (du, dv) in self.allowedMovementCodes.items():
			u, v = currentState.cell
			while True:
				x, y = u + du, v + dv
				if self.isCellOutsideGrid( (x, y) ) or (u, v, x, y) in self.blockedMoves:
					break
				u, v = x, y
			adjacentCell = u, v
			move = Move( moveCode=directionTag, moveDistance=None )
			newSearchState = SearchState( adjacentCell, previousMove=move, previousState=currentState )
			adjacentStateList.append( newSearchState )
		return adjacentStateList

	def getCacheEntryFromSearchState( self, searchState ):
		return searchState.cell

	def getStartState( self ):
		return SearchState( self.startCell, previousMove=None, previousState=None )

	def isTargetState( self, currentState ):
		return currentState.isTargetCell( self.targetCell )

	def solve( self, startCellNumber, targetCellNumber ):
		self.startCell, self.targetCell = self._convertCellNumber( startCellNumber ), self._convertCellNumber( targetCellNumber )

		searchState = self.breadthFirstSearch()
		pathString, _ = self.getPath( searchState )

		return pathString

class JumpingLabyrinthTest( unittest.TestCase ):
	def _readMaze( self, filename ):
		with open( 'tests/Labyrinth/{}'.format( filename ) ) as inputFile:
			rows, cols = map( int, inputFile.readline().strip().split() )
			startCellNumber, targetCellNumber = map( int, inputFile.readline().strip().split() )
			blockingCellList = list()
			for inputLine in inputFile.readlines():
				for token in inputLine.strip().split():
					blockingCellList.append( token )
			return rows, cols, startCellNumber, targetCellNumber, blockingCellList

	def _verify( self, testcaseFile, expectedSolutionDict ):
		rows, cols, startCellNumber, targetCellNumber, blockingCellList = self._readMaze( testcaseFile )
		mazeName = testcaseFile
		
		labyrinth = Labyrinth( rows, cols, blockingCellList, mazeName=mazeName )
		pathString = labyrinth.solve( startCellNumber, targetCellNumber )

		prettyPathString = ''.join( map( lambda token : token.strip(), pathString.split( ':' ) ) )
		pathLength = len( pathString.split( ':' ) )
		print( 'Labyrinth: mazeName = {} Path : {} Length = {}'.format( mazeName, prettyPathString, pathLength ) )

		self.assertEqual( pathLength, expectedSolutionDict[ testcaseFile ] )

	def _readSolutionFile( self, solutionFileName ):
		expectedSolutionDict = dict()
		with open( 'tests/Labyrinth/{}.ans'.format( solutionFileName ) ) as solutionFile:
			for solutionLine in solutionFile.readlines():
				testcaseFile, expectedMoveCount = solutionLine.strip().split( ':' )
				expectedSolutionDict[ testcaseFile.strip() ] = int( expectedMoveCount )
		return expectedSolutionDict

	def test_solve( self ):
		testcaseFiles = set()
		for testcaseFile in os.listdir( 'tests/Labyrinth' ):
			testcaseFiles.add( Path( testcaseFile ).stem )

		solutionFileName = 'Solution'
		testcaseFiles.remove( solutionFileName )
		expectedSolutionDict = self._readSolutionFile( solutionFileName )
		
		for testcaseFile in testcaseFiles:
			self._verify( testcaseFile, expectedSolutionDict )

if __name__ == '__main__':
	unittest.main()