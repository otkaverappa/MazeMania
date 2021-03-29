import unittest
import os
from pathlib import Path
import itertools
import copy

from StateSpaceSearch import (StateSpaceSearch, Maze, MazeLayout, SearchState, Movement, Move, BaseMazeInterface)

class MazeOfLifeSearchState( SearchState ):
	def __init__( self, blueCell, aliveCellList, previousMove, previousState ):
		SearchState.__init__( self, cell=None, previousMove=previousMove, previousState=previousState )
		self.blueCell = blueCell
		self.aliveCellList = sorted( aliveCellList )

class MazeOfLifeConfig:
	def __init__( self, rows, cols, startCellNumber, targetCellNumber, aliveCellNumberList ):
		self.rows, self.cols = rows, cols
		self.startCellNumber, self.targetCellNumber = startCellNumber, targetCellNumber
		self.aliveCellNumberList = aliveCellNumberList

class MazeOfLife( BaseMazeInterface, StateSpaceSearch ):
	def __init__( self, mazeOfLifeConfig, mazeName=None ):
		BaseMazeInterface.__init__( self, mazeOfLifeConfig.rows, mazeOfLifeConfig.cols )

		self.allowedMovementCodes =  copy.deepcopy( Movement.horizontalOrVerticalMovementCode )
		self.allowedMovementCodes.update( Movement.diagonalMovementCode )
		self.allowedMovementCodes.update( Movement.noMovementCode )

		self.startCell = self.convertCellNumber( mazeOfLifeConfig.startCellNumber )
		self.targetCell = self.convertCellNumber( mazeOfLifeConfig.targetCellNumber )

		self.aliveCellList = list( map( self.convertCellNumber, mazeOfLifeConfig.aliveCellNumberList ) )

	def _nextGeneration( self, aliveCellSet ):
		cellsToEvaluate = set()
		for u, v in aliveCellSet:
			for du, dv in self.allowedMovementCodes.values():
				adjacentCell = u + du, v + dv
				cellsToEvaluate.add( adjacentCell )

		nextGenerationAliveCells = copy.deepcopy( aliveCellSet )
		for cellToEvaluate in cellsToEvaluate:
			if self.isCellOutsideGrid( cellToEvaluate ):
				continue
			count = 0
			u, v = cellToEvaluate
			for du, dv in self.allowedMovementCodes.values():
				if du == 0 and dv == 0:
					continue
				adjacentCell = u + du, v + dv
				if adjacentCell in aliveCellSet:
					count = count + 1
			cellAlive = cellToEvaluate in aliveCellSet
			if cellAlive and ( count < 2 or count > 3 ):
				nextGenerationAliveCells.remove( cellToEvaluate )
			elif not cellAlive and count == 3:
				nextGenerationAliveCells.add( cellToEvaluate )
		return nextGenerationAliveCells

	def getAdjacentStateList( self, currentState ):
		adjacentStateList = list()		

		blueCell, aliveCellList = currentState.blueCell, currentState.aliveCellList

		aliveCellSet = set( aliveCellList )
		for directionTag, (du, dv) in self.allowedMovementCodes.items():
			u, v = blueCell
			newBlueCell = u + du, v + dv

			if self.isCellOutsideGrid( newBlueCell ) or newBlueCell in aliveCellSet:
				continue

			aliveCellSet.add( newBlueCell )
			nextGenerationAliveCells = self._nextGeneration( aliveCellSet )
			aliveCellSet.remove( newBlueCell )
			
			if newBlueCell in nextGenerationAliveCells:
				nextGenerationAliveCells.remove( newBlueCell )
				move = Move( moveCode=directionTag, moveDistance=None )
				newSearchState = MazeOfLifeSearchState( newBlueCell, list( nextGenerationAliveCells ),
				                                        previousMove=move, previousState=currentState )
				adjacentStateList.append( newSearchState )
		
		return adjacentStateList

	def getCacheEntryFromSearchState( self, searchState ):
		aliveCellTuple = tuple( searchState.aliveCellList )
		return (searchState.blueCell, aliveCellTuple)

	def getStartState( self ):
		return MazeOfLifeSearchState( self.startCell, self.aliveCellList, previousMove=None, previousState=None )

	def isTargetState( self, currentState ):
		return currentState.blueCell == self.targetCell

	def solve( self ):
		searchState = self.breadthFirstSearch()
		pathString, _ = self.getPath( searchState )

		return pathString

class MazeOfLifeTest( unittest.TestCase ):
	def _readMaze( self, filename ):
		with open( 'tests/MazeOfLife/{}'.format( filename ) ) as inputFile:
			rows, cols = map( int, inputFile.readline().strip().split() )
			startCellNumber, targetCellNumber = map( int, inputFile.readline().strip().split() )
			aliveCellNumberList = map( int, inputFile.readline().strip().split( ',' ) )

			return MazeOfLifeConfig( rows, cols, startCellNumber, targetCellNumber, aliveCellNumberList )

	def _verify( self, testcaseFile, expectedSolutionDict ):
		marbleMazeConfig = self._readMaze( testcaseFile )
		mazeName = testcaseFile
		
		marbleMaze = MazeOfLife( marbleMazeConfig, mazeName=mazeName )
		pathString = marbleMaze.solve()

		pathLength = len( pathString.split( ':' ) )
		print( 'MazeOfLife: mazeName = {} Path : {} Length = {}'.format( mazeName, pathString, pathLength ) )

		#self.assertEqual( pathLength, expectedSolutionDict[ testcaseFile ] )

	def _readSolutionFile( self, solutionFileName ):
		expectedSolutionDict = dict()
		with open( 'tests/MazeOfLife/{}.ans'.format( solutionFileName ) ) as solutionFile:
			for solutionLine in solutionFile.readlines():
				testcaseFile, expectedMoveCount = solutionLine.strip().split( ':' )
				expectedSolutionDict[ testcaseFile.strip() ] = int( expectedMoveCount )
		return expectedSolutionDict

	def test_solve( self ):
		testcaseFiles = set()
		for testcaseFile in os.listdir( 'tests/MazeOfLife' ):
			testcaseFiles.add( Path( testcaseFile ).stem )

		solutionFileName = 'Solution'
		testcaseFiles.remove( solutionFileName )
		expectedSolutionDict = self._readSolutionFile( solutionFileName )
		
		for testcaseFile in testcaseFiles:
			self._verify( testcaseFile, expectedSolutionDict )

if __name__ == '__main__':
	unittest.main()