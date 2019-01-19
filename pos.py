from typing import Dict, List, Optional, Tuple
from .paradigm_helpers import AccentedTuple, GramInfo, oa
from .utils import first_vowel_index, last_vowel_index, indices, insert

def _swap(trunk_: str, AP: str) -> str:
   # this function swaps last vowel of given trunk
   # from long to short and vice versa

   trunk_lvi = last_vowel_index(trunk_)
   last_macron = trunk_.rfind('\u0304')

   if trunk_lvi: # if the word has vowels (otherwise, do nothing):
      if AP.endswith(':') and trunk_lvi+1 != last_macron and trunk_lvi+2 != last_macron:
      # if we need to insert macron, we do it
         word_form = insert(trunk_, {trunk_lvi+2: '\u0304'})

      elif AP.endswith('.') and trunk_lvi+1 != last_macron and last_macron != -1:
      # and vice versa, we delete macron from the last vowel in case it is there
         word_form = trunk_[:last_macron] + trunk_[last_macron+1:] 

      else:
         word_form = trunk_
         #print(f'word {word_form} got vowels, but macron is ahead of middle dot!')
   else:
      word_form = trunk_
   return word_form

def _apply_neocirk(word_form: str,
                   lvi: Optional[int],
                   fvi: Optional[int],
                   pvi: Optional[int],
                   morpheme: str,
                   case: int) -> List[str]: 

   # neocircumflex is accent retraction from a newly long vowel;
   # this function returns only one tuple, unlike _delete_left_bracket
   for i in range(case):
      if '\u030d' not in word_form:
         if lvi is not None:
            word_form = insert(word_form, {lvi+1: '\u030d'})
            morpheme = morpheme.replace('·', '') # no further possibilities to accentize it
      elif lvi is not None and pvi is not None:
         #word_form = insert(word_form, {lvi+1: '\u0304'}) #macronize last vowel
         word_form = word_form.replace('\u030d', '') # delete accent mark
         word_form = insert(word_form, {pvi+1: '\u030d'}) # add accent mark after pvi
         morpheme = morpheme.replace('·', '') 
      #else:
         #raise IndexError(f"{word_form} has not enough vowels for this operation")
   result = [word_form, morpheme]
   return result

class PartOfSpeech():
   def __init__(self, key: str, kind: str, info: str, yat:str="ekav") -> None:
      self.key = key
      self.gram = GramInfo(kind, info.split(';'))

   def accentize(self, current_AP: str, word: str) -> str:
      if current_AP not in oa:
         word = word.replace('\u030d', '')
         if '\u030d' not in word: # straight
            word = word.replace('·', '\u030d', 1) # to straight
      else:
         word = word.replace('·', '')
      return word

   def swap(self, trunk_: str, length_inconstant: bool, AP: str, target_AP: str) -> str:
      # at first we process words like boos ~ bosa
      if length_inconstant and AP == target_AP:
         word_form = _swap(trunk_, AP)
      # this part is about words where length is the same in most forms:
      else:
         word_form = trunk_
      return word_form

   def _delete_right_bracket(self, word_form: str, morpheme: str, current_AP: str) -> Tuple[str, str]:
      if morpheme.startswith('>') and current_AP not in ['d:', 'e:']:
         word_form = word_form.replace('\u0304', '')
      morpheme = morpheme.replace('>', '')
      return word_form, morpheme

   def _delete_left_bracket(self, word_form: str, morpheme: str, accent: str, current_AP: str) -> List[List[str]]:
      connectenda = []
      if morpheme.startswith('<'): # so far only '-ā' is like that
         # 1. handling yers and defining if the word has neocircumflex:
         # if morpheme is genitive -ā (so far the only one with '<'),
         # stem has mobile vowel, ending is accented,
         # gender is not feminine (i.e. m/n),
         # and, at last, word is not komunizam-like exception (a.p. q),
         # then word DOES have neocircumflex retraction
         # and yer is FORCEDLY clarified to an 'a' sound;
         # other yers will be handled afterwards by the common yer rule
         #
         # without yers, in cases like jèzik : jȅzīkā:
         # stem has no mobile vowel, stem is accented,
         # word is not feminine, accented vowel is not the first one

         # 2. finding vowel places that will be of importance
         lvi, fvi, pvi = indices(word_form)

         if ('ъ' in word_form \
            and current_AP in accent \
            and 'q' not in current_AP \
            and 'm' in self.gram.other or 'n' in self.gram.other):
            retraction = [2]
         elif pvi is not None and ('ъ' not in word_form \
            and current_AP not in accent \
            and 'm' in self.gram.other or 'n' in self.gram.other \
            and not '\u030d' in word_form[pvi+2:]):
            retraction = [1]
         elif 'm' in self.gram.other and 'œв' in word_form \
            and 'c' in current_AP:
            retraction = [1, 0] # бо̏го̄ва̄, бо̀го̄ва̄, бого́ва̄
         elif 'm' in self.gram.other and 'œв' in word_form \
            and 'b' in current_AP:
            retraction = [2, 1] # гро̏ше̄ва̄ & гро̀ше̄ва̄
         else:
            retraction = [0]

         word_form = word_form.replace('ъ', 'а')

         # a renewed set of indices, since ъ has become а
         lvi, fvi, pvi = indices(word_form)

         # 3. handling strange new exceptions like komunizam
         if '·' in word_form and current_AP == 'q.' and lvi:
            word_form = insert(word_form.replace('·', ''), {lvi: '·'})

         # 4. we insert macron after lvi if last vowel is short
         if not '\u0304' in word_form[lvi:] and lvi is not None:
            word_form = insert(word_form, {lvi+1: '\u0304'}).replace('\u0304·', '·\u0304')

         # 5. if we have neocircumflex retraction, we apply it
         for case in retraction:
            connectenda.append(_apply_neocirk(word_form, lvi, fvi, pvi, morpheme, case))

         if retraction == [False]:
            # 6. in some cases (TODO: when??) we delete all straight accents and reinsert a new one at pvi
            if lvi != fvi and '\u0304\u030d' in word_form[lvi:] \
                  and not '\u0304' in word_form[:lvi] \
                  and not 'q' in current_AP \
                  and not 'c?' in current_AP:
               if pvi is not None:
                  word_form = word_form.replace('\u030d', '')
                  word_form = insert(word_form, {pvi+1: '\u030d'})
               # 7. and we raise IndexError if it is not possible
               else:
                  raise IndexError(f"{word_form} has not enough vowels for this operation")
      else:
         connectenda = [[word_form, morpheme]]
      for pair in connectenda:
         pair[1] = pair[1].replace('<', '')
      return connectenda

   def _append_morpheme(self, current_AP: str, word_form: List[str], ending_part: AccentedTuple) -> List[str]:

      connectenda: List[List[str]] = []

      for word_subform in word_form:

         morpheme = ending_part.morpheme
         accent = ending_part.accent
         # deleting the first of two accents (is it OK to have it here?)
         if current_AP in accent and '\u030d' in word_subform:
            word_subform = word_subform.replace('\u030d', '')

         # first we delete '>' (= delete all macrons in the word)
         # then we delete '<' (= lengthen the last vowel in the stem)

         word_subform, morpheme = self._delete_right_bracket(word_subform, morpheme, current_AP)
         connectenda += self._delete_left_bracket(word_subform, morpheme, accent, current_AP)

      # if this ending_part IS ACCENTED in this AP,
      # then first we delete the now unnecessary accent in the stem in case it is there;
      # second we put the accent into the ending_part,
      # the word hereby being accented;
      # and if it shouldn't, we just do nothing and leave it unaccented;
      # after that, we append the morpheme
      # TODO: understand all this "in [paradigm list]" stuff;
      # I already see it is needed here, but it seems unlogical

      for pair in connectenda:
         # accentizing 
         if current_AP in ending_part.accent:
            #if self.gram.AP[i] not in ['c?']:
            #word_form = word_form.replace('\u030d', '') # straight
            if '\u030d' in word_form and not '0' in pair[1]: # TODO: provide example for this
               pair[1] = pair[1].replace('·', '')
            if 'q' in current_AP:
               pair[1] = pair[1].replace('0', '')
            pair[1] = pair[1].replace('·', '\u030d') # to straight
            pair[0] = pair[0].replace('·', '')
         # accentizing enclinomena (words without accent)
         elif all([x not in current_AP for x in ['o', 'a', 'b', 'e']]) \
         and '\u030d' not in pair[0]:
            _fvi = first_vowel_index(pair[0])
            if  _fvi is not None:
               pair[0] = insert(pair[0], {_fvi: '\u030d'})
         
      result = [pair[0]+pair[1] for pair in connectenda]
      return result
