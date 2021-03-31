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

	def positionsAttacked( chessPiece, fromPosition, dimension ):
		scanLine, anyDistance = ChessPiece.getScanLineDistance( chessPiece.pieceName )
		rows, cols = dimension

		attackedCells = set()

		u, v = fromPosition
		for du, dv in scanLine:
			distance = 1
			while True:
				x, y = u + du * distance, v + dv * distance
				if not 0 <= x < rows or not 0 <= y < cols:
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
			attackedCells = ChessPiece.positionsAttacked( chessPieceToPlace, cell, self.dimension )
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

if __name__ == '__main__':
	unittest.main()