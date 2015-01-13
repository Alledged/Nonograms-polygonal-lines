def gcd(u, v):
    """Euclid's algorithm for computing greatest common denominator."""
    r = u % v
    while r != 0:
        u = v
        v = r
        r = u % v
    return v

class Rational:
    """Represents a rational number with arbitrary precision.

    Instances are immutable and automatically reduced, with nonnegative denominator.
    """
    def __init__(self, numerator=0, denominator=1):
        """Constructs a new rational value.

        numerator   (default 0)
        denominator (default 1)
        """
        if isinstance(numerator, Rational):
            denominator *= numerator.getDenominator()
            numerator = numerator.getNumerator()
        if isinstance(denominator,Rational):
            numerator *= denominator.getDenominator()
            denominator = denominator.getNumerator()
        
        if isinstance(numerator, (int,long)) and isinstance(denominator, (int,long)):
            if denominator == 0:                   # fraction is undefined
                self._numer = 0
                self._denom = 0
            else:
                factor = gcd( abs(numerator), abs(denominator) )
                if denominator < 0:                  # want to divide through by negated factor
                    factor = -factor
                self._numer = numerator // factor
                self._denom = denominator // factor
        else:
            raise TypeError('numerator and denominator for rational must be integral.')

    ########  Accessors  ########
    def getNumerator(self):
        """Return numerator."""
        return self._numer

    def getDenominator(self):
        """Return denominator."""
        return self._denom

    def isUndefined(self):
        """Return true if undefined value."""
        return self._denom == 0

    ########  Arithmetic Methods  ########
    def __add__(self, other):
        """Return a new rational that is the sum of two given instances."""
        if isinstance(other,(int,long)):
            other = Rational(other)
        return Rational(self._numer * other._denom + self._denom * other._numer, self._denom * other._denom)

    def __sub__(self, other):
        """Return a new rational that is the difference between two given instances."""
        if isinstance(other,(int,long)):
            other = Rational(other)
        return Rational(self._numer * other._denom - self._denom * other._numer, self._denom * other._denom)

    def __pos__(self):
        """Returns itself."""
        return self

    def __neg__(self):
        """Returns a new rational that is the negation of given instance."""
        return Rational(-self._numer, self._denom)

    def __mul__(self, other):
        """Return a new rational that is the product of two given instances."""
        if isinstance(other,(int,long)):
            other = Rational(other)
        return Rational(self._numer * other._numer, self._denom * other._denom)

    def __div__(self, other):
        """Returns a new rational that is the quotient of two given instances."""
        if isinstance(other,(int,long)):
            other = Rational(other)
        return Rational(self._numer * other._denom, self._denom * other._numer)

    def __radd__(self, other):
        return self + other
    
    def __rsub__(self, other):
        return Rational(other) - self

    def __rmul__(self, other):
        return self * other
    
    def __rdiv__(self, other):
        return Rational(other) / self

    def __abs__(self):
        """Return rational representing absolute value."""
        return Rational(abs(self._numer), self._denom)
        
    def __pow__(self, exp):
        """Return rational raised to given exponent.

        If exponent is integral, result is still a rational.
        If exponent is floating-point, result is floating point.
        """
        if isinstance(exp, (int,long)):
            if exp >= 0:
                return Rational(self._numer ** exp, self._denom ** exp)
            else:  # invert
                return Rational(self._denom ** exp, self._numer ** exp)
        else:
            return float(self) ** exp
        
    
    ########  Comparison Methods  ########
    def __cmp__(self, other):
        """Compare two rationals.

        ValueError is raised if either value is Undefined.
        """
        if isinstance(other, (int,long)):
            return cmp(self._numer, self._denom * other)
        elif isinstance(other, Rational):
            if self._denom != 0 != other._denom:
                return cmp(self._numer * other._denom, self._denom * other._numer)
            else:
                raise ValueError('Comparison involving undefined rational value.')
        else:
            raise TypeError('Cannot compare rational to given object')

    ########  Type Conversion Methods  ########
    def __float__(self):
        """Return a float approximating the current rational number."""
        return float(self._numer) / self._denom

    def __int__(self):
        """Return an integer by truncating the current rational."""
        return int(float(self))                # convert to float, then truncate
  
    def __repr__(self):
        """Returns a string representation of the rational.

        If the denominator is one, it is not displayed.
        If the rational is undefined, 'Undefined' is returned.
        """
        if self._denom == 0:
            return 'Undefined'
        elif self._denom == 1:
            return str(self._numer)
        else:
            return str(self._numer) + '/' + str(self._denom)
