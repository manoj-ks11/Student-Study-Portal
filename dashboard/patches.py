from youtubesearchpython.handlers.componenthandler import ComponentHandler
from youtubesearchpython.core.constants import videoElementKey, channelElementKey, playlistElementKey, shelfElementKey, richItemKey
from youtubesearchpython.core.search import SearchCore

# 1. Monkeypatch youtubesearchpython to fix TypeError when channel['id'] or video['id'] is None.
def patched_getVideoComponent(self, element: dict, shelfTitle: str = None) -> dict:
    video = element[videoElementKey]
    video_id = self._getValue(video, ['videoId']) or ''
    channel_id = self._getValue(video, ['ownerText', 'runs', 0, 'navigationEndpoint', 'browseEndpoint', 'browseId']) or ''
    
    component = {
        'type':                           'video',
        'id':                             video_id,
        'title':                           self._getValue(video, ['title', 'runs', 0, 'text']),
        'publishedTime':                   self._getValue(video, ['publishedTimeText', 'simpleText']),
        'duration':                        self._getValue(video, ['lengthText', 'simpleText']),
        'viewCount': {
            'text':                        self._getValue(video, ['viewCountText', 'simpleText']),
            'short':                       self._getValue(video, ['shortViewCountText', 'simpleText']),
        },
        'thumbnails':                      self._getValue(video, ['thumbnail', 'thumbnails']),
        'richThumbnail':                   self._getValue(video, ['richThumbnail', 'movingThumbnailRenderer', 'movingThumbnailDetails', 'thumbnails', 0]),
        'descriptionSnippet':              self._getValue(video, ['detailedMetadataSnippets', 0, 'snippetText', 'runs']),
        'channel': {
            'name':                        self._getValue(video, ['ownerText', 'runs', 0, 'text']),
            'id':                          channel_id,
            'thumbnails':                  self._getValue(video, ['channelThumbnailSupportedRenderers', 'channelThumbnailWithLinkRenderer', 'thumbnail', 'thumbnails']),
        },
        'accessibility': {
            'title':                       self._getValue(video, ['title', 'accessibility', 'accessibilityData', 'label']),
            'duration':                    self._getValue(video, ['lengthText', 'accessibility', 'accessibilityData', 'label']),
        },
    }
    component['link'] = f'https://www.youtube.com/watch?v={video_id}'
    component['channel']['link'] = f'https://www.youtube.com/channel/{channel_id}'
    component['shelfTitle'] = shelfTitle
    return component

ComponentHandler._getVideoComponent = patched_getVideoComponent


# 2. Monkeypatch SearchCore._getComponents to prevent 'NoneType' object is not iterable/subscriptable errors.
def patched_getComponents(self, findVideos: bool, findChannels: bool, findPlaylists: bool) -> None:
    self.resultComponents = []
    if not self.responseSource:
        return
        
    for element in self.responseSource:
        if not isinstance(element, dict):
            continue
            
        # Optimization: short-circuit with flags and use direct key membership check (O(1)) instead of .keys() view
        if findVideos and videoElementKey in element:
            try:
                self.resultComponents.append(self._getVideoComponent(element))
            except Exception:
                pass
                
        if findChannels and channelElementKey in element:
            try:
                self.resultComponents.append(self._getChannelComponent(element))
            except Exception:
                pass
                
        if findPlaylists and playlistElementKey in element:
            try:
                self.resultComponents.append(self._getPlaylistComponent(element))
            except Exception:
                pass
                
        if findVideos and shelfElementKey in element:
            shelf_comp = self._getShelfComponent(element)
            shelf_elements = shelf_comp.get('elements') if shelf_comp else None
            if shelf_elements and isinstance(shelf_elements, list):
                for shelfElement in shelf_elements:
                    try:
                        self.resultComponents.append(
                            self._getVideoComponent(shelfElement, shelfTitle=shelf_comp.get('title')))
                    except Exception:
                        pass
                        
        if findVideos and richItemKey in element:
            richItemElement = self._getValue(element, [richItemKey, 'content'])
            if isinstance(richItemElement, dict) and videoElementKey in richItemElement:
                try:
                    self.resultComponents.append(self._getVideoComponent(richItemElement))
                except Exception:
                    pass
                    
        if len(self.resultComponents) >= self.limit:
            break

SearchCore._getComponents = patched_getComponents
