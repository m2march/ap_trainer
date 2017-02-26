\version "2.7.40"
\header {
	composer = "Trad.               "
	crossRefNumber = "1                   "
	footnotes = ""
	tagline = "Lily was here 2.18.2 -- automatically converted from ABC"
	title = "Dusty Miller, The"
}
voicedefault =  {
\set Score.defaultBarType = ""

\repeat volta 2 {
%  tune no 1
 %  title
 %  traditional
 %  meter
 \time 3/4                  \tempo 4=100 %  key
 \key g \major   b'8.    c''16    d''8    b'8    a'8    g'8  \bar "|"   fis'8   
 a'8    a'8    c''8    b'8    a'8  \bar "|"   b'8.    c''16    d''8    b'8    
a'8    g'8  \bar "|"   d'8    g'8    g'8    b'8    a'8    g'8  }     b'8    
d''8    d''8    g''8    fis''8    g''8  \bar "|"   a''8    a'8    a'8    c''8   
 b'8    a'8  \bar "|"   b'8    d''8    d''8    g''8    fis''8    a''8  \bar "|" 
  g''8    g'8    g'8    b'8    a'8    g'8  }     b'8    g'8    g'16    g'16    
g'8    b'8    g'8  \bar "|"   fis'8    a'8    a'8    c''8    b'8    a'8  
\bar "|"   b'8    g'8    g'16    g'16    g'8    b'8    g'8  \bar "|"   d'8    
g'8    g'8    b'8    a'8    g'8  }   
}

\score{
    <<

	\context Staff="default"
	{
	    \voicedefault 
	}

    >>
	\layout {
	}
	\midi {}
}
