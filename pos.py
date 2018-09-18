from typing import Any, Dict, List
from .paradigm_helpers import AccentedTuple, GramInfo, nice_name, oa
from .utils import swap_length

class PartOfSpeech():
   def __init__(self, key: str, value: Dict[str, Any]) -> None:
      self.key = key 
      self.value = value 
      i, t = self.value['i'].split(';'), self.value['t'] 
      self.info = GramInfo(i, t) 

   def _swap(self, trunk_: str, length_inconstant: bool, AP: str, target_AP: str) -> str:
      # at first we process words like boos ~ bosa
      if length_inconstant and AP == target_AP:
         word_form = swap_length(trunk_, AP)
      # this part is about words where length is the same in most forms:
      else:
         word_form = trunk_
      return word_form

   def _append_morpheme(self, i: int, word_form: str, ending_part: AccentedTuple) -> str:
      # if this ending_part should be accented in this AP,
      # then first we delete the now unnecessary accent in the stem in case it is there;
      # second we put the accent into the ending_part,
      # the word hereby being accented;
      # and if it shouldn't, we just do nothing and leave it unaccented;
      # after that, we append the morpheme
      if self.info.AP[i] in ending_part.accent:
         if self.info.AP[i] in oa:
            word_form = word_form.replace('\u030d', '') # straight
         morpheme = ending_part.morpheme.replace('·', '\u030d') # to straight
      else:
         morpheme = ending_part.morpheme
      return word_form + morpheme

   def _reduce_doublets(self, endings_: List[List[AccentedTuple]], AP: str) -> List[List[AccentedTuple]]:
      # necessary in verbs and nouns;
      # not needed in adjectives.
      # it deletes endings identical in future
      ready_endings: List[Any] = []
      if len(endings_) > 1:
         for ending_ in endings_:
            addendum = True
            
            supr_ = ''.join([x.morpheme for x in ending_]).replace('·', '')
            for ending in ready_endings:
               supr = ''.join([d.morpheme for d in ending]).replace('·', '')
               accents_ = ''.join([z.accent for z in ending])
               if AP not in accents_ and supr_ == supr:
                  addendum = False
            if addendum:   
               ready_endings.append(ending_)
      else:
         ready_endings = endings_
         
      return ready_endings