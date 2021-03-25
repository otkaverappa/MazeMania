import unittest
import os
from pathlib import Path
import itertools

from StateSpaceSearch import (StateSpaceSearch, Maze, MazeLayout, SearchState, Movement, Move, BaseMazeInterface)

class MarbleMazeSearchState( SearchState ):
	def __init__( self, redMarbleCellList, blackMarbleCellList, previousMove=None, previousState=None ):
		SearchState.__init__( self, cell=None, previousMove=previousMove, previousState=previousState )
		self.redMarbleCellList = sorted( redMarbleCellList )
		self.blackMarbleCellList = sorted( blackMarbleCellList )

	def isTargetState( self ):
		return len( self.redMarbleCellList ) == 0

class MarbleMazeConfig:
	def __init__( self, rows, cols, redMarblePositionList, blackMarblePositionList,
		          targetCellNumber, blockingCellList ):
		self.rows, self.cols = rows, cols
		self.redMarblePositionList = redMarblePositionList
		self.blackMarblePositionList = blackMarblePositionList
		self.targetCellNumber = targetCellNumber
		self.blockingCellList = blockingCellList

class MarbleMaze( BaseMazeInterface, StateSpaceSearch ):
	def __init__( self, marbleMazeConfig, mazeName=None ):
		self.marbleMazeConfig = marbleMazeConfig
		BaseMazeInterface.__init__( self, self.marbleMazeConfig.rows, self.marbleMazeConfig.cols )

		self.allowedMovementCodes =  Movement.horizontalOrVerticalMovementCode

		self.blockedMoves = set()

		for blockingCellInfo in self.marbleMazeConfig.blockingCellList:
			fromCellNumber, directionString = blockingCellInfo.split( ':' )
			u, v = self._convertCellNumber( int( fromCellNumber ) )
			for directionTag in directionString:
				du, dv = self.allowedMovementCodes[ directionTag ]
				x, y = u + du, v + dv
				# We cannot move from (u, v) to (x, y) and from (x, y) to (u, v).
				cell1, cell2 = (u, v), (x, y)
				self.blockedMoves.add( (cell1, cell2) )
				self.blockedMoves.add( (cell2, cell1) )

		self.redMarbleCellList = list( map( self._convertCellNumber, self.marbleMazeConfig.redMarblePositionList ) )
		self.blackMarbleCellList = list( map( self._convertCellNumber, self.marbleMazeConfig.blackMarblePositionList ) )
		self.targetCell = self._convertCellNumber( self.marbleMazeConfig.targetCellNumber )

		self.scanOrderDict = dict()
		rowRange, colRange = range( self.rows ), range( self.cols )
		self.scanOrderDict[ 'N' ] = list( itertools.product( rowRange, colRange ) )
		self.scanOrderDict[ 'S' ] = list( itertools.product( reversed( rowRange ), colRange ) )
		self.scanOrderDict[ 'E' ] = list( itertools.product( rowRange, reversed( colRange ) ) )
		self.scanOrderDict[ 'W' ] = list( itertools.product( rowRange, colRange ) )

	def _convertCellNumber( self, cellNumber ):
		cellNumber = cellNumber - 1
		return (cellNumber // self.cols, cellNumber % self.cols)

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()		
		
		occupiedCellDict = dict()
		for cell in currentState.redMarbleCellList:
			occupiedCellDict[ cell ] = 'RED'
		for cell in currentState.blackMarbleCellList:
			occupiedCellDict[ cell ] = 'BLACK'

		for directionTag, (du, dv) in self.allowedMovementCodes.items():
			newOccupiedCellDict = dict()

			for row, col in self.scanOrderDict[ directionTag ]:
				if (row, col) not in occupiedCellDict:
					continue
				# A marble is present in (row, col). Move it as far as possible in the direction specified by directionTag.
				# Also, check whether the marble reaches the target cell.
				marbleInTargetCell = False
				newCell = u, v = row, col
				
				while True:
					nextCell = u + du, v + dv
					if self.isCellOutsideGrid( nextCell ) or (newCell, nextCell) in self.blockedMoves or nextCell in newOccupiedCellDict:
						break
					newCell = u, v = nextCell
					if newCell == self.targetCell:
						marbleInTargetCell = True
						break
				
				# newCell is the cell to which we have to move the marble at (row, col). If marbleInTargetCell
				# is True, then it disappears and is not added to newOccupiedCellDict.
				if not marbleInTargetCell:
					newOccupiedCellDict[ newCell ] = occupiedCellDict[ (row, col) ]

			newRedMarbleCellList = list()
			newBlackMarbleCellList = list()
			for cell, color in newOccupiedCellDict.items():
				cellList = newRedMarbleCellList if color == 'RED' else newBlackMarbleCellList
				cellList.append( cell )

			move = Move( moveCode=directionTag, moveDistance=None )
			newSearchState = MarbleMazeSearchState( newRedMarbleCellList, newBlackMarbleCellList, previousMove=move,
				                                    previousState=currentState )
			adjacentStateList.append( newSearchState )
		return adjacentStateList

	def getCacheEntryFromSearchState( self, searchState ):
		redMarblePositionTuple = tuple( searchState.redMarbleCellList )
		blackMarblePositionTuple = tuple( searchState.blackMarbleCellList )
		return (redMarblePositionTuple, blackMarblePositionTuple)

	def getStartState( self ):
		return MarbleMazeSearchState( self.redMarbleCellList, self.blackMarbleCellList )

	def isTargetState( self, currentState ):
		return currentState.isTargetState()

	def solve( self ):
		searchState = self.breadthFirstSearch()
		pathString, _ = self.getPath( searchState )

		return pathString

class MarbleMazeTest( unittest.TestCase ):
	def _readMaze( self, filename ):
		with open( 'tests/MarbleMaze/{}'.format( filename ) ) as inputFile:
			rows, cols = map( int, inputFile.readline().strip().split() )

			token, positionList = inputFile.readline().strip().split( '=' )
			assert token.strip() == 'red_marbles'
			redMarblePositionList = list( map( int, positionList.strip().split( ',' ) ) )
			
			token, positionList = inputFile.readline().strip().split( '=' )
			assert token.strip() == 'black_marbles'
			blackMarblePositionList = list( map( int, positionList.strip().split( ',' ) ) )
			
			token, cellNumber = inputFile.readline().strip().split( '=' )
			assert token.strip() == 'target'
			targetCellNumber = int( cellNumber.strip() )

			blockingCellList = list()
			for inputLine in inputFile.readlines():
				for token in inputLine.strip().split():
					blockingCellList.append( token )
			
			return MarbleMazeConfig( rows, cols, redMarblePositionList, blackMarblePositionList, targetCellNumber,
			                         blockingCellList )

	def _verify( self, testcaseFile, expectedSolutionDict ):
		marbleMazeConfig = self._readMaze( testcaseFile )
		mazeName = testcaseFile
		
		marbleMaze = MarbleMaze( marbleMazeConfig, mazeName=mazeName )
		pathString = marbleMaze.solve()

		prettyPathString = ''.join( map( lambda token : token.strip(), pathString.split( ':' ) ) )
		pathLength = len( pathString.split( ':' ) )
		print( 'MarbleMaze: mazeName = {} Path : {} Length = {}'.format( mazeName, prettyPathString, pathLength ) )

		#self.assertEqual( pathLength, expectedSolutionDict[ testcaseFile ] )

	def _readSolutionFile( self, solutionFileName ):
		expectedSolutionDict = dict()
		with open( 'tests/MarbleMaze/{}.ans'.format( solutionFileName ) ) as solutionFile:
			for solutionLine in solutionFile.readlines():
				testcaseFile, expectedMoveCount = solutionLine.strip().split( ':' )
				expectedSolutionDict[ testcaseFile.strip() ] = int( expectedMoveCount )
		return expectedSolutionDict

	def test_solve( self ):
		testcaseFiles = set()
		for testcaseFile in os.listdir( 'tests/MarbleMaze' ):
			testcaseFiles.add( Path( testcaseFile ).stem )

		solutionFileName = 'Solution'
		testcaseFiles.remove( solutionFileName )
		expectedSolutionDict = self._readSolutionFile( solutionFileName )
		
		for testcaseFile in testcaseFiles:
			self._verify( testcaseFile, expectedSolutionDict )

if __name__ == '__main__':
	unittest.main()