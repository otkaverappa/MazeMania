import unittest
import itertools
import copy

class ChessPiece:
	ROOK, KNIGHT, BISHOP, QUEEN, KING, PAWN = 'ROOK', 'KNIGHT', 'BISHOP', 'QUEEN', 'KING', 'PAWN'
	pieceToTokenMap = {
	ROOK : 'R', KNIGHT : 'k', BISHOP : 'B', QUEEN : 'Q', KING : 'K', PAWN : 'P'
	}
	tokenToPieceMap = {
	'R' : ROOK, 'k' : KNIGHT, 'B' : BISHOP, 'Q' : QUEEN, 'K' : KING, 'P' : PAWN
	}

	def __init__( self, pieceName ):
		self.pieceName = pieceName
		self.position = None

	def __repr__( self ):
		return ChessPiece.pieceToTokenMap[ self.pieceName ]

	def positionsAttacked( self, fromPosition, dimension, blockedCells=None ):
		scanLine, anyDistance = ChessPiece.getScanLineDistance( self.pieceName )
		rows, cols = dimension

		attackedCells = set()

		u, v = fromPosition
		for du, dv in scanLine:
			distance = 1
			while True:
				x, y = u + du * distance, v + dv * distance
				if not 0 <= x < rows or not 0 <= y < cols:
					break
				if blockedCells is not None and (x, y) in blockedCells:
					break
				attackedCells.add( (x, y) )
				distance += 1
				if not anyDistance:
					break
		return attackedCells

	@staticmethod
	def getScanLineDistance( pieceName ):
		horizontalScanLine = [ (0, 1), (0, -1 ) ]
		verticalScanLine = [ (1, 0), (-1, 0) ]
		diagonalScanLine = [ (1, 1), (1, -1), (-1, 1), (-1, -1) ]
		knightScanLine = [ (1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1) ]

		scanLineDict = {
		ChessPiece.ROOK   : horizontalScanLine + verticalScanLine,
		ChessPiece.KNIGHT : knightScanLine,
		ChessPiece.BISHOP : diagonalScanLine,
		ChessPiece.QUEEN  : horizontalScanLine + verticalScanLine + diagonalScanLine,
		ChessPiece.KING   : horizontalScanLine + verticalScanLine + diagonalScanLine,
		}

		anyDistanceDict = {
		ChessPiece.ROOK   : True,
		ChessPiece.KNIGHT : False,
		ChessPiece.BISHOP : True,
		ChessPiece.QUEEN  : True,
		ChessPiece.KING   : False 
		}

		return scanLineDict[ pieceName ], anyDistanceDict[ pieceName ]

class Rook( ChessPiece ):
	def __init__( self ):
		ChessPiece.__init__( self, pieceName=ChessPiece.ROOK )

class Knight( ChessPiece ):
	def __init__( self ):
		ChessPiece.__init__( self, pieceName=ChessPiece.KNIGHT )

class Bishop( ChessPiece ):
	def __init__( self ):
		ChessPiece.__init__( self, pieceName=ChessPiece.BISHOP )

class Queen( ChessPiece ):
	def __init__( self ):
		ChessPiece.__init__( self, pieceName=ChessPiece.QUEEN )

class King( ChessPiece ):
	def __init__( self ):
		ChessPiece.__init__( self, pieceName=ChessPiece.KING )

class Pawn( ChessPiece ):
	def __init__( self ):
		ChessPiece.__init__( self, pieceName=ChessPiece.PAWN )

class ChessPieceFactory:
	chessPieceDict = {
	ChessPiece.ROOK   : Rook(),
	ChessPiece.KNIGHT : Knight(),
	ChessPiece.BISHOP : Bishop(),
	ChessPiece.QUEEN  : Queen(),
	ChessPiece.KING   : King(),
	ChessPiece.PAWN   : Pawn()
	}

	@staticmethod
	def get( pieceName ):
		return ChessPieceFactory.chessPieceDict[ pieceName ]

class ChessAvoidance:
	def __init__( self, board, chessPieceInfoString ):
		self.dimension = self.rows, self.cols = len( board ), len( board[ 0 ] )
		self.emptyCells = set()

		self.emptyCellToken, self.blockedCellToken = '.', '#'

		for (row, col) in itertools.product( range( self.rows ), range( self.cols ) ):
			if board[ row ][ col ] == self.emptyCellToken:
				self.emptyCells.add( (row, col) )

		self.chessPieceList = list()
		
		tokenToPieceMap = ChessPiece.tokenToPieceMap
		for token in chessPieceInfoString:
			self.chessPieceList.append( ChessPieceFactory.get( tokenToPieceMap[ token ] ) )

	def _search( self, chessPieceIndex, emptyCells, chessPiecesPlacedDict ):
		if chessPieceIndex == len( self.chessPieceList ):
			return True

		chessPieceToPlace = self.chessPieceList[ chessPieceIndex ]
		# Try to place the chess piece in one of the emptyCells.
		occupiedCells = set( chessPiecesPlacedDict.keys() )
		
		for cell in list( emptyCells ):
			attackedCells = chessPieceToPlace.positionsAttacked( cell, self.dimension )
			if len( set.intersection( attackedCells, occupiedCells ) ) == 0:
				# We can place the chess piece at this location. Remove attackedCells as well
				# as the current cell from emptyCells.
				attackedCells.add( cell )
				newEmptyCells = set.difference( emptyCells, attackedCells )
				
				chessPiecesPlacedDict[ cell ] = chessPieceToPlace
				searchSuccessful = self._search( chessPieceIndex + 1, newEmptyCells, chessPiecesPlacedDict )
				if searchSuccessful:
					return True
				del chessPiecesPlacedDict[ cell ]				
		return False

	def avoid( self ):
		emptyCells = copy.deepcopy( self.emptyCells )
		chessPiecesPlacedDict = dict()
		self._search( 0, emptyCells, chessPiecesPlacedDict )

		avoidanceBoard = list()
		for row in range( self.rows ):
			rowString = str()
			for col in range( self.cols ):
				if (row, col) in chessPiecesPlacedDict:
					token = repr( chessPiecesPlacedDict[ (row, col) ] )
				elif (row, col) in self.emptyCells:
					token = self.emptyCellToken
				else:
					token = self.blockedCellToken
				rowString = rowString + token
			avoidanceBoard.append( rowString )
		return avoidanceBoard

class ChessAvoidanceTest( unittest.TestCase ):
	def _verify( self, board, chessPieceInfoString, expectedAvoidanceBoard ):
		avoidanceBoard = ChessAvoidance( board, chessPieceInfoString ).avoid()
		self.assertEqual( avoidanceBoard, expectedAvoidanceBoard )

	def test_ChessAvoidance( self ):
		board = [
		'#...',
		'....',
		'....'
		]
		chessPieceInfoStringList = [ 'BBBBQ', 'KKkkR', 'BBKKkk' ]
		expectedAvoidanceBoardList = [
		[ '#.BB', 'Q...', '..BB' ],
		[ '#k.K', 'R...', '.k.K' ],
		[ '#K.K', '....', 'BkBk' ]
		]

		for chessPieceInfoString, expectedAvoidanceBoard in zip( chessPieceInfoStringList, expectedAvoidanceBoardList ):
			self._verify( board, chessPieceInfoString, expectedAvoidanceBoard )

		board = [
		'#..##',
		'.....',
		'.....'
		]
		chessPieceInfoStringList = [ 'BkQQ', 'KkQR', 'kkkQ', 'kkkRR', 'BKKkQ', 'BBBBkk', 'BBBKkR' ]
		expectedAvoidanceBoardList = [
		[ '#Q.##', '...Bk', 'Q....' ],
		[ '#Q.##', '...R.', 'K...k' ],
		[ '#k.##', 'kk...', '....Q' ],
		[ '#R.##', 'k.k.k', '...R.' ],
		[ '#Q.##', '....B', 'K.K.k' ],
		[ '#B.##', '....B', 'BkB.k' ],
		[ '#K.##', '....R', 'BBBk.' ]
		]

		for chessPieceInfoString, expectedAvoidanceBoard in zip( chessPieceInfoStringList, expectedAvoidanceBoardList ):
			self._verify( board, chessPieceInfoString, expectedAvoidanceBoard )

		board = [
		'#...',
		'#...',
		'#...',
		'....'
		]
		chessPieceInfoStringList = [ 'KkQQ', 'BKkkQ', 'KKkRR', 'KKKkkk', 'BBBBBkk' ]
		expectedAvoidanceBoardList = [
		[ '#Q..', '#..Q', '#...', 'k.K.' ],
		[ '#Q..', '#..K', '#...', 'k.Bk' ],
		[ '#..K', '#R..', '#.R.', 'K..k' ],
		[ '#K.K', '#...', '#..k', 'K.kk' ],
		[ '#BBk', '#...', '#...', 'kBBB' ]
		]
		
		for chessPieceInfoString, expectedAvoidanceBoard in zip( chessPieceInfoStringList, expectedAvoidanceBoardList ):
			self._verify( board, chessPieceInfoString, expectedAvoidanceBoard )
		
		board = [
		'#....',
		'.....',
		'.....'
		]
		chessPieceInfoStringList = [ 'KKkkQ', 'BBBkkR', 'KKkkkR', 'BBBBkR', 'BBkkkkR' ]
		expectedAvoidanceBoardList = [
		[ '#.K.k', 'Q....', '..K.k' ],
		[ '#B..k', '...R.', 'BB..k' ],
		[ '#.k.K', '.R...', 'k.k.K' ],
		[ '#..BB', '.R...', 'k..BB' ],
		[ '#.R..', 'Bk.kB', 'k...k' ]
		]
		
		for chessPieceInfoString, expectedAvoidanceBoard in zip( chessPieceInfoStringList, expectedAvoidanceBoardList ):
			self._verify( board, chessPieceInfoString, expectedAvoidanceBoard )

class ChessPath:
	def __init__( self, board ):
		self.dimension = self.rows, self.cols = len( board ), len( board[ 0 ] )
		self.startPosition, self.targetPosition = (self.rows - 1, 0), (0, self.cols - 1)

		self.chessPieceDict = dict()
		for row, col in itertools.product( range( self.rows ), range( self.cols ) ):
			token = board[ row ][ col ]
			if token in ChessPiece.tokenToPieceMap:
				self.chessPieceDict[ (row, col) ] = ChessPieceFactory.get( ChessPiece.tokenToPieceMap[ token ] )

		self.chessPiecePositionSet = set( self.chessPieceDict.keys() )

		self.board = list()
		for boardRow in board:
			self.board.append( list( boardRow ) )
		
		self.adjacentCellList = [ (0, 1), (0, -1), (1, 0), (-1, 0) ]
		self.diagonalAdjacentCellList = [ (1, 1), (1, -1), (-1, 1), (-1, -1) ]
		self.emptyCellToken, self.pathCellToken = '.', '#'

	def _touch( self, cell, visited ):
		visitedAdjacentCells = list()

		u, v = cell
		for du, dv in self.adjacentCellList + self.diagonalAdjacentCellList:
			cell = u + du, v + dv
			if cell in visited:
				visitedAdjacentCells.append( cell )
		if len( visitedAdjacentCells ) > 2:
			return True
		elif len( visitedAdjacentCells ) < 2:
			return False
		(r1, c1), (r2, c2) = visitedAdjacentCells
		return r1 != r2 and c1 != c2

	def _search( self, currentPosition, visited ):
		cell = row, col = currentPosition

		visited.add( (row, col) )
		self.board[ row ][ col ] = self.pathCellToken

		if currentPosition == self.targetPosition:
			attackedCellCount = None
			for position, chessPiece in self.chessPieceDict.items():
				attackedCells = chessPiece.positionsAttacked( position, self.dimension, self.chessPiecePositionSet )
				# How many attackedCells are in visited ?
				count = len( set.intersection( attackedCells, visited ) )
				if attackedCellCount is None:
					attackedCellCount = count
				elif count != attackedCellCount:
					# We have reached an invalid state.
					self.board[ row ][ col ] = self.emptyCellToken
					visited.remove( cell )
					return False
			return True

		# Try to move to an adjacent cell.
		for du, dv in self.adjacentCellList:
			newCell = x, y = row + du, col + dv
			if not 0 <= x < self.rows or not 0 <= y < self.cols:
				continue
			if newCell in visited or newCell in self.chessPieceDict:
				continue
			if self._touch( newCell, visited ):
				continue
			
			pathFound = self._search( newCell, visited )
			if pathFound:
				return True

		self.board[ row ][ col ] = self.emptyCellToken
		visited.remove( cell )		
		return False

	def path( self ):
		visited = set()

		self._search( self.startPosition, visited )
		
		# The board is a list of lists. Convert it into a list of strings.
		for row in range( self.rows ):
			self.board[ row ] = ''.join( self.board[ row ] )

		return self.board

class BoardReader:
	@staticmethod
	def read( inputFile ):
		rows, cols = map( int, inputFile.readline().strip().split() )
		board = list()
		if not rows == cols == 0:
			for _ in range( rows ):
				board.append( inputFile.readline().strip() )
			inputFile.readline()
		return rows, cols, board

class ChessPathTest( unittest.TestCase ):
	def _render( self, boardWithPath ):
		for rowString in boardWithPath:
			print( rowString )
		print()

	def test_ChessPath( self ):
		expectedBoardWithPathList = list()
		with open ('tests/ChessPath.ans' ) as solutionFile:
			while True:
				rows, cols, boardWithPath = BoardReader.read( solutionFile )
				if rows == cols == 0:
					break
				expectedBoardWithPathList.append( boardWithPath )

		index = 0
		with open( 'tests/ChessPath' ) as inputFile:
			while True:
				rows, cols, board = BoardReader.read( inputFile )
				if rows == cols == 0:
					break

				expectedBoardWithPath = expectedBoardWithPathList[ index ]
				index += 1
				
				print( 'Testcase #{} rows = {} cols = {}'.format( index, rows, cols ) )
				boardWithPath = ChessPath( board ).path()
				
				self._render( boardWithPath )
				self.assertEqual( boardWithPath, expectedBoardWithPath )

class RookEndMaze:
	def __init__( self, board ):
		pass

	def path( self ):
		pass

class RookEndMazeTest( unittest.TestCase ):
	def test_RookEndMaze( self ):
		index = 0
		with open( 'tests/RookEndMaze' ) as inputFile:
			while True:
				rows, cols, board = BoardReader.read( inputFile )
				if rows == cols == 0:
					break

				index += 1

				print( 'Testcase #{} rows = {} cols = {}'.format( index, rows, cols ) )
				RookEndMaze( board ).path()

if __name__ == '__main__':
	unittest.main()